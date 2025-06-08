import React, { useEffect, useRef } from 'react';
import styles from './MessageList.module.css';
import MessageItem from '../MessageItem/MessageItem';
import type { Message, ImageResult } from '../ChatPage/ChatPage';

interface MessageListProps {
  messages: Message[];
  isOldMessages?: boolean;
  onImageClick?: (image: ImageResult) => void;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isOldMessages, onImageClick }) => {
  const messagesEndRef = useRef<null | HTMLDivElement>(null);
  const messageListRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (!isOldMessages && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: "smooth",
        block: "end"
      });
    }
  };

  useEffect(() => {
    if (!isOldMessages && messages.length > 0) {
      // Small delay to ensure DOM is updated
      setTimeout(scrollToBottom, 100);
    }
  }, [messages, isOldMessages]);

  return (
    <div 
      ref={messageListRef} 
      className={`${styles.messageList} ${isOldMessages ? styles.oldMessageList : ''}`}
    >
      {messages.map((msg) => (
        <MessageItem
          key={msg.id}
          text={msg.text}
          sender={msg.sender}
          isDimmed={isOldMessages}
          image={msg.image}
          images={msg.images}
          onImageClick={onImageClick}
        />
      ))}
      {!isOldMessages && <div ref={messagesEndRef} />}
    </div>
  );
};

export default MessageList;
