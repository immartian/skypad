import React, { useState, useEffect, useMemo } from 'react';
import styles from './ChatPage.module.css';
import StatusIndicator from '../StatusIndicator/StatusIndicator';
import MessageList from '../MessageList/MessageList';
import MessageInput from '../MessageInput/MessageInput';
import OntologyVisualization from '../OntologyVisualization/OntologyVisualization';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bella';
  image?: string; // Base64 data URL or file path
  imageFile?: File; // Original file for analysis
}

const BELLA_EMOJI = '🧘‍♀️'; // Or any other emoji/icon

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<string>('Online');
  const [showWorkspace, setShowWorkspace] = useState(false); // Start with visualization hidden
  const [isGuest, setIsGuest] = useState(true); // Track authentication state
  const [isDragging, setIsDragging] = useState(false); // Track drag state
  const [focusedEntities, setFocusedEntities] = useState<string[]>([]); // Track ontology focus

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        { id: 'init-bella', text: "Hi, Bella here. Please feel free to ask me any questions about Skypad AI system powered by RE theory. Also you can try to upload furniture images to analyze its style.", sender: 'bella' }
      ]);
    }
  }, []); // Removed messages from dependency array to avoid re-triggering

  const handleSendMessage = async (text: string) => {
    // Extract entities from user message and update focus
    const entities = extractEntitiesFromText(text);
    if (entities.length > 0) {
      setFocusedEntities(entities);
      // Show visualization when entities are detected
      if (!showWorkspace) {
        setShowWorkspace(true);
      }
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
    };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    console.log('Setting status to: Bella is typing...');
    setStatus('Bella is typing...');

    try {
      // Use relative URL that will work both locally and in Cloud Run
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: text,
          focused_entities: entities // Send focused entities to backend
        }),
      });

      if (!response.ok) {
        let errorDetail = 'Network response was not ok.';
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorDetail;
        } catch (jsonError) {
          errorDetail = response.statusText || errorDetail;
        }
        throw new Error(errorDetail);
      }

      const data = await response.json();
      
      // Extract entities from Bella's response too
      const bellaEntities = extractEntitiesFromText(data.reply);
      if (bellaEntities.length > 0) {
        setFocusedEntities(prev => [...new Set([...prev, ...bellaEntities])]);
        // Show visualization when Bella mentions entities
        if (!showWorkspace) {
          setShowWorkspace(true);
        }
      }

      const bellaMessage: Message = {
        id: Date.now().toString() + '-bella',
        text: data.reply,
        sender: 'bella',
      };

      setMessages((prevMessages) => [...prevMessages, bellaMessage]);
      setStatus('Online');
    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMessageText = error instanceof Error ? error.message : 'Sorry, I had trouble responding. Please try again.';
      const errorMessage: Message = {
        id: Date.now().toString() + '-error',
        text: errorMessageText,
        sender: 'bella',
      };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
      setStatus('Error communicating with Bella');
    }
  };

  // Image handling functions
  const analyzeImageWithOpenAI = async (imageFile: File): Promise<string> => {
    try {
      const base64 = await fileToBase64(imageFile);
      const response = await fetch('/api/analyze-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          image: base64,
          prompt: "Please analyze this image and provide a brief description of its style, colors, and main elements. Focus on design and aesthetic aspects."
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze image');
      }

      const data = await response.json();
      return data.analysis || 'Image uploaded successfully.';
    } catch (error) {
      console.error('Image analysis error:', error);
      return 'Image uploaded successfully, but analysis is temporarily unavailable.';
    }
  };

  const fileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = error => reject(error);
    });
  };

  const handleImageUpload = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file.');
      return;
    }

    try {
      const imageDataUrl = await fileToBase64(file);
      
      // Add user message with image
      const userMessage: Message = {
        id: Date.now().toString(),
        text: `[Image uploaded: ${file.name}]`,
        sender: 'user',
        image: imageDataUrl,
        imageFile: file,
      };
      setMessages((prevMessages) => [...prevMessages, userMessage]);
      setStatus('Bella is typing...');

      // Analyze image and get Bella's response
      const analysis = await analyzeImageWithOpenAI(file);
      
      const bellaMessage: Message = {
        id: Date.now().toString() + '-bella',
        text: analysis,
        sender: 'bella',
      };

      setMessages((prevMessages) => [...prevMessages, bellaMessage]);
      setStatus('Online');
    } catch (error) {
      console.error('Image upload error:', error);
      setStatus('Error processing image');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setIsDragging(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleImageUpload(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleImageUpload(file);
    }
    // Reset the input so the same file can be uploaded again
    e.target.value = '';
  };

  const { oldMessages, recentMessages } = useMemo(() => {
    const RECENT_COUNT = 3; // Show a few more recent messages
    if (messages.length <= RECENT_COUNT) {
      return { oldMessages: [], recentMessages: messages };
    }
    return {
      oldMessages: messages.slice(0, messages.length - RECENT_COUNT),
      recentMessages: messages.slice(messages.length - RECENT_COUNT),
    };
  }, [messages]);

  const handleBackgroundClick = () => {
    console.log('Background clicked!', { showWorkspace, innerWidth: window.innerWidth });
    // Only activate workspace if clicked on background workspace area and desktop
    if (window.innerWidth >= 768 && !showWorkspace) {
      console.log('Activating workspace mode...');
      setShowWorkspace(true);
    }
  };

  const handleBellaClick = () => {
    // Bella click toggles workspace mode (collapses chat to show workspace)
    if (!showWorkspace) {
      setShowWorkspace(true);
    }
  };

  const handleInputFocus = () => {
    // Keep visualization visible in the background - no need to change states
  };

  const handleUserIconClick = () => {
    if (isGuest) {
      // Simulate OAuth login
      alert('OAuth login would trigger here (Google, GitHub, etc.)');
      setIsGuest(false);
    } else {
      // Show user profile/settings
      alert('User profile/settings would open here');
    }
  };

  // Entity extraction function
  const extractEntitiesFromText = (text: string): string[] => {
    // Known entities from our ontology
    const knownEntities = [
      'TheDorian', 'CHILDesign', 'ConcordHospitality', 'Bedframe_123', 
      'UrbanHotel', 'GuestRoom', 'Sleep', 'Project', 'Designer', 
      'FurnitureItem', 'Client', 'PurchasingAgent',
      // Add common terms that would indicate ontology discussion
      'ontology', 'entity', 'relationship', 'knowledge graph'
    ];
    
    const foundEntities: string[] = [];
    const textLower = text.toLowerCase();
    
    knownEntities.forEach(entity => {
      const entityLower = entity.toLowerCase();
      // Check for exact match
      if (textLower.includes(entityLower)) {
        foundEntities.push(entity);
      }
      // Check for camelCase or PascalCase converted to spaces
      else if (textLower.includes(entityLower.replace(/([A-Z])/g, ' $1').trim())) {
        foundEntities.push(entity);
      }
      // Check for snake_case converted to spaces
      else if (entityLower.includes('_') && textLower.includes(entityLower.replace(/_/g, ' '))) {
        foundEntities.push(entity);
      }
    });
    
    return foundEntities;
  };

  return (
    <div className={`${styles.chatPage} ${showWorkspace ? styles.workspaceMode : ''}`}>
      {/* Background Workspace - Always visible, dimmed when inactive */}
      <div 
        className={`${styles.backgroundWorkspace} ${showWorkspace ? styles.active : styles.dimmed}`}
        onClick={handleBackgroundClick}
      >
        <div className={styles.workspaceContent} onClick={(e) => {
          e.stopPropagation();
          // Also allow clicking on workspace content to activate workspace mode
          if (!showWorkspace && window.innerWidth >= 768) {
            console.log('Workspace content clicked, activating workspace...');
            setShowWorkspace(true);
          }
        }}>
          <div className={styles.leftPane}>
            <h3>RE Skypad</h3>
            <div className={styles.threadList}>
              <div className={styles.threadItem}>🏗️ Projects (8/902)</div>
              <div className={styles.threadItem}>🎨 Design (3 live)</div>
              <div className={styles.threadItem}>🏪 Vendors (5 live)</div>
              <div className={styles.threadItem}>📢 Marketing (2 campaigns)</div>
              <div className={styles.threadItem}>💡 Ideas (1 live)</div>
              <div className={styles.threadItem}>📊 Analytics (4 live)</div>
            </div>
          </div>
          <div className={styles.centerPane}>
            {showWorkspace ? (
              <div className={styles.fullVisualizationContainer}>
                <OntologyVisualization 
                  focusedEntities={focusedEntities}
                  onNodeClick={(node) => {
                    // When user clicks a node, add it to chat context
                    const entityName = node.name;
                    const contextMessage = `Tell me about ${entityName}`;
                    handleSendMessage(contextMessage);
                  }}
                />
              </div>
            ) : (
              <>
                <h3>Skypad Ontology Visualization</h3>
                <p>Mention entities like "Project", "Designer", "FurnitureItem" in your chat to see related visualizations.</p>
                <div className={styles.placeholderContent}>
                  <div className={styles.contentBlock}>
                    <h4>Available Entity Types</h4>
                    <p>• Projects & Design Work</p>
                    <p>• Furniture Items & Categories</p>
                    <p>• Clients & Relationships</p>
                  </div>
                </div>
              </>
            )}
          </div>
          <div className={styles.rightPane}>
            <h3>Context & AI</h3>
            <p>AI insights and related resources appear here</p>
            <div className={styles.aiInsights}>
              <div className={styles.insightItem}>🤖 Bella's Analysis</div>
              <div className={styles.insightItem}>📎 Related Files</div>
              <div className={styles.insightItem}>🔗 Quick Actions</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div 
        className={`${styles.chatContainer} ${showWorkspace ? styles.collapsed : ''} ${isDragging ? styles.dragging : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Bella Avatar - Upper Left with File Tray */}
        <div className={styles.bellaZone}>
          <div className={styles.bellaAvatar} onClick={handleBellaClick}>{BELLA_EMOJI}</div>
          <StatusIndicator status={status} />
          {/* Removed the visualization toggle button to keep UI minimal */}
          
          {/* File Upload Tray - Near Bella */}
          <div className={styles.fileTray} onClick={(e) => {
            e.stopPropagation();
            // Trigger file input click
            const fileInput = document.getElementById('imageFileInput') as HTMLInputElement;
            fileInput?.click();
          }}>
            <input
              id="imageFileInput"
              type="file"
              accept="image/*"
              style={{ display: 'none' }}
              onChange={handleFileInputChange}
            />
            <div className={styles.trayContent}>
              <div className={styles.trayIcon}>🖼️</div>
              <span className={styles.trayText}>Images</span>
            </div>
          </div>
        </div>

        {/* Messages Area - Hidden when collapsed */}
        <div className={styles.messagesArea}>
          {/* Dimmed old messages */}
          <div className={styles.oldMessagesArea}>
            <MessageList messages={oldMessages} isOldMessages={true} />
          </div>
          
          {/* Recent messages */}
          <div className={styles.recentMessagesArea}>
            <MessageList messages={recentMessages} />
          </div>
        </div>

        {/* Input Area with User Icon - Always visible */}
        <div 
          className={styles.inputArea}
          onClick={(e) => {
            e.stopPropagation();
            // Expand chat when clicking the input area if collapsed
            if (showWorkspace) {
              setShowWorkspace(false);
            }
          }}
        >
          <MessageInput 
            onSendMessage={handleSendMessage} 
            onFocus={handleInputFocus}
          />
          <div 
            className={`${styles.userIcon} ${isGuest ? styles.guestIcon : ''}`}
            onClick={(e) => {
              e.stopPropagation();
              handleUserIconClick();
            }}
            title={isGuest ? "Click to sign in" : "User profile"}
          >
            {isGuest ? '👤' : '👨‍💼'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
