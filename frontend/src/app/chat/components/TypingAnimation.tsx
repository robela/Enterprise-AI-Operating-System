import React from "react";

const TypingAnimation = () => {
  return (
    <div className="typing-animation">
      <span className="dot" />
      <span className="dot" />
      <span className="dot" />

      <style jsx>{`
        .typing-animation {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 50px;
          height: 24px;
        }

        .dot {
          background-color: #999;
          border-radius: 50%;
          width: 8px;
          height: 8px;
          margin: 0 2px;
          animation: typing-animation 1s infinite;
        }

        .dot:nth-child(2) {
          animation-delay: 0.2s;
        }

        .dot:nth-child(3) {
          animation-delay: 0.4s;
        }

        @keyframes typing-animation {
          0% {
            opacity: 0.2;
          }
          20% {
            opacity: 1;
          }
          100% {
            opacity: 0.2;
          }
        }
      `}</style>
    </div>
  );
};

export default TypingAnimation;
