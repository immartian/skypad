import React, { useState, useEffect, useMemo } from 'react';
import styles from './ChatPage.module.css';
import StatusIndicator from '../StatusIndicator/StatusIndicator';
import MessageList from '../MessageList/MessageList';
import MessageInput from '../MessageInput/MessageInput';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bella';
  image?: string; // For future image support
}

const BELLA_EMOJI = '🧘‍♀️'; // Or any other emoji/icon

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<string>('Online');
  const [showWorkspace, setShowWorkspace] = useState(false);
  const [isGuest, setIsGuest] = useState(true); // Track authentication state

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        { id: 'init-bella', text: "Hi! I'm Bella. How can I help you today?", sender: 'bella' }
      ]);
    }
  }, []); // Removed messages from dependency array to avoid re-triggering

  const handleSendMessage = async (text: string) => {
    // If chat is collapsed, expand it first
    if (showWorkspace) {
      setShowWorkspace(false);
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
    };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setStatus('Bella is thinking...');

    try {
      // Use relative URL that will work both locally and in Cloud Run
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
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
    // Expand chat when user focuses on input while collapsed
    if (showWorkspace) {
      setShowWorkspace(false);
    }
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
            <h3>Thread Content</h3>
            <p>Click a thread to view discussions and AI insights...</p>
            <div className={styles.placeholderContent}>
              <div className={styles.contentBlock}>
                <h4>Recent Activity</h4>
                <p>• New design concepts uploaded</p>
                <p>• Vendor quotes received</p>
                <p>• Marketing campaign ideas</p>
              </div>
            </div>
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
        className={`${styles.chatContainer} ${showWorkspace ? styles.collapsed : ''}`}
      >
        {/* Bella Avatar - Upper Left with File Tray */}
        <div className={styles.bellaZone} onClick={handleBellaClick}>
          <div className={styles.bellaAvatar}>{BELLA_EMOJI}</div>
          <StatusIndicator status={status} />
          
          {/* File Upload Tray - Near Bella */}
          <div className={styles.fileTray} onClick={(e) => e.stopPropagation()}>
            <div className={styles.trayContent}>
              <div className={styles.trayIcon}>📁</div>
              <span className={styles.trayText}>Files</span>
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
