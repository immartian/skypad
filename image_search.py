"""
Simple Image Search Module
Direct semantic search for images using manual cosine similarity - no fallbacks or indexes
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import OpenAI
try:
    import openai
    HAS_OPENAI = True
    openai.api_key = os.getenv("OPENAI_API_KEY")
except ImportError:
    HAS_OPENAI = False
    print("Warning: OpenAI not available. Install with: pip install openai")


class ImageSearch:
    """Simple image search using manual cosine similarity calculation only"""
    
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
    
    def close(self):
        """Explicitly close the Neo4j driver"""
        if hasattr(self, 'driver'):
            self.driver.close()
    
    def __del__(self):
        self.close()
    
    async def _get_query_embedding(self, query: str) -> Optional[List[float]]:
        """Get embedding for search query using OpenAI"""
        if not HAS_OPENAI:
            print("OpenAI not available for embeddings")
            return None
        
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return None

    async def search_images(
        self, 
        query: str, 
        limit: int = 10, 
        min_similarity: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Search for images using semantic similarity with manual cosine calculation
        
        Args:
            query: Search query text (e.g., "modern sofa", "wooden dining table")
            limit: Maximum number of results to return
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            
        Returns:
            List of dictionaries with 'path', 'description', and 'similarity_score'
        """
        query_embedding = await self._get_query_embedding(query)
        if not query_embedding:
            print("Could not generate embedding for query")
            return []

        with self.driver.session() as session:
            cypher_query = """
                MATCH (i:Image)
                WHERE i.embedding_vector IS NOT NULL
                WITH i, 
                     reduce(dot = 0.0, j IN range(0, size(i.embedding_vector)-1) | 
                         dot + (i.embedding_vector[j] * $query_vector[j])) as dot_product,
                     sqrt(reduce(norm_a = 0.0, a IN i.embedding_vector | norm_a + a * a)) as norm_a,
                     sqrt(reduce(norm_b = 0.0, b IN $query_vector | norm_b + b * b)) as norm_b
                WITH i, dot_product / (norm_a * norm_b) as similarity
                WHERE similarity >= $min_similarity
                RETURN i.path as path, 
                       i.description as description, 
                       similarity as similarity_score
                ORDER BY similarity DESC
                LIMIT $limit
            """
            
            try:
                result = session.run(cypher_query, {
                    'query_vector': query_embedding,
                    'min_similarity': min_similarity,
                    'limit': limit
                })
                
                images = []
                for record in result:
                    images.append({
                        'path': record['path'],
                        'description': record['description'] or 'No description',
                        'similarity_score': round(record['similarity_score'], 4)
                    })
                
                return images
                
            except Exception as e:
                print(f"Error executing search query: {e}")
                return []
    
    async def find_similar_images(
        self, 
        reference_image_path: str, 
        limit: int = 10, 
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Find images similar to an existing image in the database
        
        Args:
            reference_image_path: Path to the reference image
            limit: Maximum number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar images with similarity scores
        """
        with self.driver.session() as session:
            cypher_query = """
                MATCH (ref:Image {path: $ref_path})
                WHERE ref.embedding_vector IS NOT NULL
                MATCH (other:Image)
                WHERE other.embedding_vector IS NOT NULL AND other.path <> $ref_path
                WITH other, ref,
                     reduce(dot = 0.0, j IN range(0, size(ref.embedding_vector)-1) | 
                         dot + (ref.embedding_vector[j] * other.embedding_vector[j])) as dot_product,
                     sqrt(reduce(norm_a = 0.0, a IN ref.embedding_vector | norm_a + a * a)) as norm_a,
                     sqrt(reduce(norm_b = 0.0, b IN other.embedding_vector | norm_b + b * b)) as norm_b
                WITH other, dot_product / (norm_a * norm_b) as similarity
                WHERE similarity >= $min_similarity
                RETURN other.path as path,
                       other.description as description,
                       similarity as similarity_score
                ORDER BY similarity DESC
                LIMIT $limit
            """
            
            try:
                result = session.run(cypher_query, {
                    'ref_path': reference_image_path,
                    'min_similarity': min_similarity,
                    'limit': limit
                })
                
                similar_images = []
                for record in result:
                    similar_images.append({
                        'path': record['path'],
                        'description': record['description'] or 'No description',
                        'similarity_score': round(record['similarity_score'], 4)
                    })
                
                return similar_images
                
            except Exception as e:
                print(f"Error finding similar images: {e}")
                return []
    
    async def get_random_images(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get random images from the database (useful for testing or discovery)
        
        Args:
            limit: Number of random images to return
            
        Returns:
            List of random images with their information
        """
        with self.driver.session() as session:
            cypher_query = """
                MATCH (i:Image)
                WHERE i.embedding_vector IS NOT NULL
                RETURN i.path as path, 
                       i.description as description
                ORDER BY rand()
                LIMIT $limit
            """
            
            try:
                result = session.run(cypher_query, {'limit': limit})
                
                images = []
                for record in result:
                    images.append({
                        'path': record['path'],
                        'description': record['description'] or 'No description'
                    })
                
                return images
                
            except Exception as e:
                print(f"Error getting random images: {e}")
                return []


# Convenience functions for easy async usage
async def search_images(query: str, limit: int = 10, min_similarity: float = 0.15) -> List[Dict[str, Any]]:
    """
    Simple async image search function
    
    Args:
        query: Search query (e.g., "modern kitchen", "wooden chair")
        limit: Maximum results to return
        min_similarity: Minimum similarity threshold
        
    Returns:
        List of matching images with similarity scores
    """
    search_engine = ImageSearch()
    try:
        results = await search_engine.search_images(query, limit, min_similarity)
        return results
    finally:
        search_engine.close()


async def find_similar_images(reference_path: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Find images similar to a reference image
    
    Args:
        reference_path: Path to the reference image
        limit: Maximum results to return
        
    Returns:
        List of similar images with similarity scores
    """
    search_engine = ImageSearch()
    try:
        results = await search_engine.find_similar_images(reference_path, limit)
        return results
    finally:
        search_engine.close()


# Synchronous wrappers for easier use
def search_images_sync(query: str, limit: int = 10, min_similarity: float = 0.15) -> List[Dict[str, Any]]:
    """Synchronous wrapper for image search"""
    return asyncio.run(search_images(query, limit, min_similarity))


def find_similar_images_sync(reference_path: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Synchronous wrapper for finding similar images"""
    return asyncio.run(find_similar_images(reference_path, limit))


# Main testing and example usage
if __name__ == "__main__":
    async def test_image_search():
        """Test the simplified image search functionality"""
        print("🔍 Testing Simple Image Search Module")
        print("=" * 60)
        
        search_engine = ImageSearch()
        
        try:
            # Test 1: Basic semantic search
            print("\n📸 Test 1: Semantic image search")
            print("-" * 30)
            
            test_queries = [
                "modern living room sofa",
                "wooden dining table",
                "kitchen cabinets",
                "bedroom furniture"
            ]
            
            for query in test_queries:
                print(f"\nSearching for: '{query}'")
                results = await search_engine.search_images(query, limit=3)
                
                if results:
                    for i, img in enumerate(results, 1):
                        print(f"  {i}. {img['path']} (Score: {img['similarity_score']})")
                        print(f"     Description: {img['description'][:80]}...")
                else:
                    print("  No results found")
            
            # Test 2: Get some random images for testing similarity
            print(f"\n📋 Test 2: Getting random images for similarity test")
            print("-" * 30)
            
            random_images = await search_engine.get_random_images(limit=3)
            if random_images:
                print(f"Found {len(random_images)} random images:")
                for i, img in enumerate(random_images, 1):
                    print(f"  {i}. {img['path']}")
                
                # Test 3: Find similar images to the first random image
                if random_images:
                    test_image = random_images[0]['path']
                    print(f"\n🔄 Test 3: Finding images similar to: {test_image}")
                    print("-" * 30)
                    
                    similar = await search_engine.find_similar_images(test_image, limit=5)
                    if similar:
                        for i, img in enumerate(similar, 1):
                            print(f"  {i}. {img['path']} (Score: {img['similarity_score']})")
                    else:
                        print("  No similar images found")
            else:
                print("  No random images found - database might be empty")
        
        except Exception as e:
            print(f"❌ Error during testing: {e}")
        
        finally:
            search_engine.close()
            print(f"\n✅ Testing completed!")
    
    # Run the comprehensive test
    asyncio.run(test_image_search())
