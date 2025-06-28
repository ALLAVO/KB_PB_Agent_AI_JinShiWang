import React from 'react';
import './IntroScreen.css';

const IntroScreen = ({ onStart }) => {
  return (
    <div className="intro-screen">
      <div className="intro-background">
        <img 
          src={require('../assets/Intro_image.png')} 
          alt="intro background" 
          className="intro-background-image"
        />
      </div>
      
      <div className="intro-content">
        <div className="intro-text">
          <h1 className="intro-title">
            이것이 <span className="highlight">진짜</span> 시황 분석이다.
          </h1>
          <h2 className="intro-subtitle">Project. 진시황</h2>
        </div>
        
        <button className="start-button" onClick={onStart}>
          시작하기
        </button>
      </div>
    </div>
  );
};

export default IntroScreen;
