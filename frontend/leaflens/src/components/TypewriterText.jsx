import { useEffect, useState } from "react";

function TypewriterText({ text }) {
  const [displayText, setDisplayText] = useState("");

  useEffect(() => {
    let i = 0;
    setDisplayText("");

    const interval = setInterval(() => {
      if (i < text.length) {
        setDisplayText(text.slice(0, i + 1));
        i++;
      } else {
        clearInterval(interval);
      }
    }, 25); 

    return () => clearInterval(interval);
  }, [text]);

  return <>{displayText}</>;
}

export default TypewriterText;