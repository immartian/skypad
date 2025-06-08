import React from 'react';
import styles from './MessageItem.module.css';
import type { ImageResult } from '../ChatPage/ChatPage';

interface MessageItemProps {
  text: string;
  sender: 'user' | 'bella';
  isDimmed?: boolean;
  image?: string; // Image data URL
  images?: ImageResult[]; // Search results images
  onImageClick?: (image: ImageResult) => void;
}

const MessageItem: React.FC<MessageItemProps> = ({ text, sender, isDimmed, image, images, onImageClick }) => {
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
      {images && images.length > 0 && (
        <div className={styles.imageGallery}>
          {images.map((img, index) => (
            <div key={index} className={styles.thumbnailContainer}>
              <img
                src={img.thumbnail_url}
                alt={img.description}
                className={styles.thumbnail}
                onClick={() => onImageClick?.(img)}
                title={`${img.description} (${(img.similarity_score * 100).toFixed(1)}% match)`}
              />
              <div className={styles.thumbnailInfo}>
                <span className={styles.similarity}>
                  {(img.similarity_score * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MessageItem;
