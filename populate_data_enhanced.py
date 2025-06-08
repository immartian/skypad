import os
import json
import csv
import base64
import hashlib
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from PIL import Image
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import OpenAI
try:
    import openai
    HAS_OPENAI = True
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        print("Warning: OpenAI API key not found in environment variables")
        HAS_OPENAI = False
except ImportError:
    print("Warning: OpenAI not installed. Image analysis will be limited.")
    HAS_OPENAI = False

class SkypadDataPopulator:
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_username = os.getenv("NEO4J_USERNAME")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not all([self.neo4j_uri, self.neo4j_username, self.neo4j_password]):
            raise ValueError("Neo4j credentials not found in environment variables")
        
        self.driver = GraphDatabase.driver(
            self.neo4j_uri, 
            auth=(self.neo4j_username, self.neo4j_password)
        )
        
        # Base paths
        self.base_path = Path("/media/im3/plus/lab4/skypad/lattice")
        self.projects_path = self.base_path / "projects"
        self.products_path = self.base_path / "products"
        self.clients_path = self.base_path / "clients"
        self.ontology_path = self.base_path / "skypad_ontology_mvp.jsonld"
    
    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.close()
    
    def clear_database(self):
        """Clear all existing data in Neo4j database"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("✓ Database cleared")
    
    def create_constraints_and_indexes(self):
        """Create necessary constraints and indexes"""
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT project_name IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE",
                "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (pr:Product) REQUIRE pr.id IS UNIQUE",
                "CREATE CONSTRAINT client_name IF NOT EXISTS FOR (c:Client) REQUIRE c.name IS UNIQUE",
                "CREATE CONSTRAINT image_path IF NOT EXISTS FOR (i:Image) REQUIRE i.path IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"Constraint creation note: {e}")
            
            # Create indexes for better search performance (do NOT index embedding_vector due to size limits)
            indexes = [
                # Description indexes
                "CREATE INDEX description_index_product IF NOT EXISTS FOR (n:Product) ON (n.description)",
                "CREATE INDEX description_index_project IF NOT EXISTS FOR (n:Project) ON (n.description)",
                "CREATE INDEX description_index_client IF NOT EXISTS FOR (n:Client) ON (n.description)",
                "CREATE INDEX description_index_image IF NOT EXISTS FOR (n:Image) ON (n.description)",
                # Domain indexes
                "CREATE INDEX domain_index_product IF NOT EXISTS FOR (n:Product) ON (n.domain)",
                "CREATE INDEX domain_index_project IF NOT EXISTS FOR (n:Project) ON (n.domain)",
                "CREATE INDEX domain_index_client IF NOT EXISTS FOR (n:Client) ON (n.domain)",
                "CREATE INDEX domain_index_image IF NOT EXISTS FOR (n:Image) ON (n.domain)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    print(f"Index creation note: {e}")
            
            print("✓ Constraints and indexes created")
    
    async def get_openai_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI's embedding model. If unsuccessful, return None (not fallback)."""
        if not HAS_OPENAI:
            return None
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding with OpenAI: {e}")
            return None
    
    async def analyze_image_with_openai(self, image_path: str) -> Dict[str, Any]:
        """Analyze image using OpenAI GPT-4 Vision and generate embedding"""
        if not HAS_OPENAI:
            return await self._generate_fallback_description(image_path)
        
        try:
            # Encode image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Prepare the API call for image analysis
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this furniture/interior design image and provide a detailed description including:
                                1. Main furniture items and their style
                                2. Color scheme and materials
                                3. Room type or setting
                                4. Design aesthetic (modern, traditional, etc.)
                                5. Notable design elements or features
                                
                                Respond in JSON format with keys: description, furniture_items, colors, materials, style, room_type, domain"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Parse JSON response
            content = response.choices[0].message.content
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                analysis = {
                    "description": content,
                    "furniture_items": [],
                    "colors": [],
                    "materials": [],
                    "style": "unknown",
                    "room_type": "unknown",
                    "domain": "furniture"
                }
            
            # Generate embedding for the description
            embedding = await self.get_openai_embedding(analysis.get('description', ''))
            analysis['embedding'] = embedding
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing image {image_path} with OpenAI: {e}")
            return await self._generate_fallback_description(image_path)
    
    async def _generate_fallback_description(self, image_path: str) -> Dict[str, Any]:
        """Generate basic description when OpenAI is not available"""
        filename = Path(image_path).stem
        
        # Extract basic info from filename
        description = f"Furniture/interior design image: {filename}"
        
        # Basic categorization based on filename patterns
        style = "modern" if any(term in filename.lower() for term in ["modern", "contemporary"]) else "traditional"
        room_type = "hotel" if "hotel" in str(image_path).lower() else "residential"
        
        # Determine domain based on path
        if "product" in str(image_path).lower():
            domain = "product"
        elif "project" in str(image_path).lower():
            domain = "project"
        else:
            domain = "furniture"
        
        # Generate embedding (will be None if OpenAI not available)
        embedding = await self.get_openai_embedding(description)
        
        return {
            "description": description,
            "furniture_items": [],
            "colors": [],
            "materials": [],
            "style": style,
            "room_type": room_type,
            "domain": domain,
            "embedding": embedding
        }
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """Process a single image file"""
        try:
            # Basic image info
            img = Image.open(image_path)
            width, height = img.size
            file_size = os.path.getsize(image_path)
            
            # Generate basic visual hash
            img_resized = img.convert('L').resize((8, 8))
            img_array = np.array(img_resized)
            visual_hash = hashlib.md5(img_array.tobytes()).hexdigest()[:16]
            
            return {
                "path": str(image_path),
                "filename": Path(image_path).name,
                "width": width,
                "height": height,
                "file_size": file_size,
                "visual_hash": visual_hash,
                "format": img.format or "unknown"
            }
            
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return None
    
    def load_ontology(self) -> Dict[str, Any]:
        """Load the Skypad ontology"""
        try:
            with open(self.ontology_path, 'r') as f:
                ontology = json.load(f)
            print(f"✓ Loaded ontology with {len(ontology)} entities")
            return ontology
        except Exception as e:
            print(f"Error loading ontology: {e}")
            return {}
    
    async def populate_clients(self):
        """Populate client data from CSV"""
        try:
            with open(self.clients_path / "clients.csv", 'r') as f:
                reader = csv.reader(f)
                clients = list(reader)
            
            with self.driver.session() as session:
                for client_data in clients:
                    if len(client_data) >= 2:
                        name = client_data[0].strip()
                        address = client_data[1].strip() if len(client_data) > 1 else ""
                        phone = client_data[2].strip() if len(client_data) > 2 else ""
                        collection = client_data[3].strip() if len(client_data) > 3 else ""
                        postal_code = client_data[4].strip() if len(client_data) > 4 else ""
                        
                        # Generate embedding for client description
                        client_text = f"{name} {address} {collection}"
                        embedding = await self.get_openai_embedding(client_text)
                        
                        session.run("""
                            MERGE (c:Client {name: $name})
                            SET c.address = $address,
                                c.phone = $phone,
                                c.collection = $collection,
                                c.postal_code = $postal_code,
                                c.description = $description,
                                c.embedding_vector = $embedding_vector,
                                c.domain = $domain,
                                c.created_at = datetime()
                        """, 
                        name=name, 
                        address=address, 
                        phone=phone, 
                        collection=collection, 
                        postal_code=postal_code,
                        description=client_text,
                        embedding_vector=embedding,
                        domain="client"
                        )
            
            print(f"✓ Populated {len(clients)} clients")
            
        except Exception as e:
            print(f"Error populating clients: {e}")
    
    async def populate_products(self):
        """Populate product data from images"""
        product_files = list(self.products_path.glob("*.png"))
        
        with self.driver.session() as session:
            for i, product_path in enumerate(product_files):
                try:
                    # Extract product ID from filename
                    filename = product_path.stem
                    product_id = filename.split('-')[0] if '-' in filename else filename
                    
                    # Process image
                    image_data = self.process_image(str(product_path))
                    if not image_data:
                        continue
                    
                    # Analyze image with OpenAI
                    analysis = await self.analyze_image_with_openai(str(product_path))
                    
                    # Generate description and embedding
                    description = analysis.get('description', f"Product {product_id} - furniture item from catalog")
                    embedding = analysis.get('embedding', None)
                    
                    # Create product node
                    session.run("""
                        MERGE (p:Product {id: $product_id})
                        SET p.name = $name,
                            p.description = $description,
                            p.embedding_vector = $embedding_vector,
                            p.domain = $domain,
                            p.style = $style,
                            p.created_at = datetime()
                    """, 
                    product_id=product_id,
                    name=f"Product {product_id}",
                    description=description,
                    embedding_vector=embedding,
                    domain="product",
                    style=analysis.get('style', 'unknown')
                    )
                    
                    # Create image node with embedding
                    session.run("""
                        MERGE (i:Image {path: $path})
                        SET i.filename = $filename,
                            i.width = $width,
                            i.height = $height,
                            i.file_size = $file_size,
                            i.visual_hash = $visual_hash,
                            i.format = $format,
                            i.description = $description,
                            i.ai_analysis = $ai_analysis,
                            i.embedding_vector = $embedding_vector,
                            i.domain = $domain,
                            i.created_at = datetime()
                    """, 
                    path=image_data['path'],
                    filename=image_data['filename'],
                    width=image_data['width'],
                    height=image_data['height'],
                    file_size=image_data['file_size'],
                    visual_hash=image_data['visual_hash'],
                    format=image_data['format'],
                    description=description,
                    ai_analysis=json.dumps(analysis),
                    embedding_vector=embedding,
                    domain="product"
                    )
                    
                    # Link product to image
                    session.run("""
                        MATCH (p:Product {id: $product_id})
                        MATCH (i:Image {path: $path})
                        MERGE (p)-[:HAS_IMAGE]->(i)
                    """, product_id=product_id, path=image_data['path'])
                    
                except Exception as e:
                    print(f"Error processing product {product_path}: {e}")
        
        print(f"✓ Populated {len(product_files)} products")
    
    async def populate_projects(self):
        """Populate project data from project folders"""
        project_folders = [d for d in self.projects_path.iterdir() if d.is_dir()]
        
        with self.driver.session() as session:
            for project_folder in project_folders:
                try:
                    project_name = project_folder.name
                    
                    # Generate project metadata
                    start_date = datetime.now() - timedelta(days=np.random.randint(30, 730))
                    end_date = start_date + timedelta(days=np.random.randint(30, 365))
                    
                    project_description = f"Interior design project: {project_name}"
                    embedding = await self.get_openai_embedding(project_description)
                    
                    # Create project node
                    session.run("""
                        MERGE (p:Project {name: $name})
                        SET p.description = $description,
                            p.start_date = $start_date,
                            p.end_date = $end_date,
                            p.status = $status,
                            p.embedding_vector = $embedding_vector,
                            p.domain = $domain,
                            p.created_at = datetime()
                    """, 
                    name=project_name,
                    description=project_description,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    status="completed",
                    embedding_vector=embedding,
                    domain="project"
                    )
                    
                    # Process project images
                    image_files = list(project_folder.glob("*.webp")) + list(project_folder.glob("*.jpg")) + list(project_folder.glob("*.png"))
                    
                    for image_path in image_files[:10]:  # Limit to 10 images per project
                        # Process image
                        image_data = self.process_image(str(image_path))
                        if not image_data:
                            continue
                        
                        # Analyze with OpenAI if available
                        analysis = await self.analyze_image_with_openai(str(image_path))
                        
                        # Generate embedding for image description
                        image_description = analysis.get('description', f"Project image: {image_path.name}")
                        image_embedding = analysis.get('embedding', None)
                        
                        # Create image node with analysis and embedding
                        session.run("""
                            MERGE (i:Image {path: $path})
                            SET i.filename = $filename,
                                i.width = $width,
                                i.height = $height,
                                i.file_size = $file_size,
                                i.visual_hash = $visual_hash,
                                i.format = $format,
                                i.description = $description,
                                i.ai_analysis = $ai_analysis,
                                i.embedding_vector = $embedding_vector,
                                i.domain = $domain,
                                i.created_at = datetime()
                        """, 
                        path=image_data['path'],
                        filename=image_data['filename'],
                        width=image_data['width'],
                        height=image_data['height'],
                        file_size=image_data['file_size'],
                        visual_hash=image_data['visual_hash'],
                        format=image_data['format'],
                        description=image_description,
                        ai_analysis=json.dumps(analysis),
                        embedding_vector=image_embedding,
                        domain="project"
                        )
                        
                        # Link project to image
                        session.run("""
                            MATCH (p:Project {name: $project_name})
                            MATCH (i:Image {path: $path})
                            MERGE (p)-[:HAS_IMAGE]->(i)
                        """, project_name=project_name, path=image_data['path'])
                
                except Exception as e:
                    print(f"Error processing project {project_folder}: {e}")
        
        print(f"✓ Populated {len(project_folders)} projects")
    
    async def populate_all_data(self):
        """Populate all data into Neo4j"""
        print("Starting Skypad data population...")
        
        # Clear and setup database
        self.clear_database()
        self.create_constraints_and_indexes()
        
        # Load ontology
        ontology = self.load_ontology()
        
        # Populate data
        await self.populate_clients()
        await self.populate_products()
        await self.populate_projects()
        
        # Create relationships based on project names and client names
        self._create_project_client_relationships()
        
        print("✓ Data population completed successfully!")
    
    def _create_project_client_relationships(self):
        """Create relationships between projects and clients based on name matching"""
        with self.driver.session() as session:
            # Link projects to clients when project names contain client keywords
            session.run("""
                MATCH (p:Project), (c:Client)
                WHERE toLower(p.name) CONTAINS toLower(split(c.name, ' ')[0])
                   OR toLower(p.name) CONTAINS toLower(c.collection)
                MERGE (c)-[:HAS_PROJECT]->(p)
            """)
            print("✓ Created project-client relationships")


class SkypadSearchEngine:
    """Enhanced search engine for Skypad data using OpenAI embeddings and domain filtering"""
    
    def __init__(self, driver):
        self.driver = driver
    
    async def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for search query"""
        if not HAS_OPENAI:
            return []
        
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return []
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def search_by_domain(self, query: str, domain: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for items using embedding similarity with optional domain filtering"""
        # Get query embedding
        query_embedding = await self.get_query_embedding(query)
        if not query_embedding:
            return await self._fallback_text_search(query, domain, limit)
        
        # Build domain filter
        domain_filter = ""
        if domain:
            domain_filter = "AND n.domain = $domain"
        
        with self.driver.session() as session:
            # Get all nodes with embeddings
            cypher_query = f"""
                MATCH (n) 
                WHERE n.embedding_vector IS NOT NULL {domain_filter}
                RETURN n, labels(n) as labels, id(n) as node_id
            """
            
            params = {}
            if domain:
                params['domain'] = domain
            
            result = session.run(cypher_query, params)
            
            scored_results = []
            
            for record in result:
                node = record['n']
                node_embedding = node.get('embedding_vector', [])
                
                if node_embedding:
                    similarity = self.cosine_similarity(query_embedding, node_embedding)
                    
                    if similarity > 0.1:  # Minimum similarity threshold
                        node_data = dict(node)
                        node_data['labels'] = record['labels']
                        node_data['similarity_score'] = similarity
                        scored_results.append(node_data)
            
            # Sort by similarity and return top results
            scored_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return scored_results[:limit]
    
    async def _fallback_text_search(self, query: str, domain: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Fallback text search when embeddings are not available"""
        domain_filter = ""
        if domain:
            domain_filter = "AND n.domain = $domain"
        
        with self.driver.session() as session:
            cypher_query = f"""
                MATCH (n) 
                WHERE n.description CONTAINS $query {domain_filter}
                RETURN n, labels(n) as labels, id(n) as node_id
                LIMIT $limit
            """
            
            params = {'query': query, 'limit': limit}
            if domain:
                params['domain'] = domain
            
            result = session.run(cypher_query, params)
            
            results = []
            for record in result:
                node_data = dict(record['n'])
                node_data['labels'] = record['labels']
                node_data['similarity_score'] = 0.5  # Default score for text matches
                results.append(node_data)
            
            return results
    
    async def smart_search(self, query: str, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Smart search that tries domain-specific search first, then global search"""
        # Detect potential domain from query
        query_lower = query.lower()
        detected_domain = None
        
        if any(term in query_lower for term in ['project', 'hotel', 'building', 'interior']):
            detected_domain = 'project'
        elif any(term in query_lower for term in ['product', 'furniture', 'chair', 'table', 'sofa']):
            detected_domain = 'product'
        elif any(term in query_lower for term in ['client', 'customer', 'company']):
            detected_domain = 'client'
        
        results = {}
        
        if detected_domain:
            # Search within detected domain first
            domain_results = await self.search_by_domain(query, detected_domain, limit)
            results[detected_domain] = domain_results
            
            # If we have good results, return them
            if domain_results and domain_results[0].get('similarity_score', 0) > 0.3:
                return results
        
        # Global search across all domains
        all_results = await self.search_by_domain(query, None, limit)
        
        # Group results by domain
        grouped_results = {}
        for result in all_results:
            domain = result.get('domain', 'unknown')
            if domain not in grouped_results:
                grouped_results[domain] = []
            grouped_results[domain].append(result)
        
        return grouped_results


# Main execution functions
async def populate_database():
    """Main function to populate the database"""
    populator = SkypadDataPopulator()
    await populator.populate_all_data()


async def search_database(query: str, domain: str = None, limit: int = 10):
    """Search the database with embedding similarity"""
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )
    
    search_engine = SkypadSearchEngine(driver)
    
    if domain:
        results = await search_engine.search_by_domain(query, domain, limit)
        return {domain: results}
    else:
        results = await search_engine.smart_search(query, limit)
        return results


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "modern furniture"
        
        # Check if domain is specified
        domain = None
        if len(sys.argv) > 3 and sys.argv[2] in ['project', 'product', 'client']:
            domain = sys.argv[2]
            query = " ".join(sys.argv[3:])
        
        results = asyncio.run(search_database(query, domain))
        
        print(f"\nSearch results for: '{query}'")
        if domain:
            print(f"Domain: {domain}")
        print("=" * 50)
        
        for domain_name, domain_results in results.items():
            if domain_results:
                print(f"\n{domain_name.upper()} RESULTS:")
                print("-" * 30)
                for i, result in enumerate(domain_results, 1):
                    print(f"{i}. {result.get('name', result.get('description', 'Unknown'))}")
                    print(f"   Labels: {', '.join(result['labels'])}")
                    print(f"   Description: {result.get('description', 'No description')[:100]}...")
                    print(f"   Similarity: {result['similarity_score']:.3f}")
                    print()
    else:
        asyncio.run(populate_database())
