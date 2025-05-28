import React from 'react';
import styles from './MessageItem.module.css';

interface MessageItemProps {
  text: string;
  sender: 'user' | 'bella';
  isDimmed?: boolean;
  image?: string; // Image data URL
}

const MessageItem: React.FC<MessageItemProps> = ({ text, sender, isDimmed, image }) => {
  const messageClass = sender === 'user' ? styles.userMessage : styles.bellaMessage;
  const dimmedClass = isDimmed ? styles.dimmedMessage : '';

  return (
    <div className={`${styles.messageItem} ${messageClass} ${dimmedClass}`}>
      {image && (
        <div className={styles.imageContainer}>
          <img 
            src={image} 
            alt="Uploaded image" 
            className={styles.messageImage}
            onClick={() => window.open(image, '_blank')}
          />
        </div>
      )}
      <p>{text}</p>
    </div>
  );
};

export default MessageItem;
