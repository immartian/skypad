import React, { useState, useEffect } from 'react';
import styles from './ChatPage.module.css';
import StatusIndicator from '../StatusIndicator/StatusIndicator';
import MessageList from '../MessageList/MessageList';
import MessageInput from '../MessageInput/MessageInput';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bella';
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    // Initial messages can be kept or removed
    // { id: '1', text: 'Hello there!', sender: 'bella' }, 
  ]);
  const [status, setStatus] = useState<string>('Online');

  // Optional: Fetch initial greeting or check status on load
  useEffect(() => {
    // You could add a health check or initial message fetch here if needed
    // e.g., fetch('http://localhost:8000/api/health').then(...)
    // For now, we just ensure Bella starts as 'Online' or a welcome message.
    if (messages.length === 0) {
        setMessages([
            { id: 'init-bella', text: "Hi! I'm Bella. How can I help you today?", sender: 'bella' }
        ]);
    }
  }, []); // Empty dependency array means this runs once on mount

  const handleSendMessage = async (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
    };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setStatus('Bella is thinking...');

    try {
      const response = await fetch('http://localhost:8000/api/chat', { // Ensure backend is running on port 8000
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
            // If parsing JSON fails, stick with the generic error or response.statusText
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

  return (
    <div className={styles.chatPage}>
      <header className={styles.header}>
        <h1>Bella Chat</h1>
        <StatusIndicator status={status} />
      </header>
      <MessageList messages={messages} />
      <MessageInput onSendMessage={handleSendMessage} />
    </div>
  );
};

export default ChatPage;
