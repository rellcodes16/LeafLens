import { useEffect, useState, useRef } from "react";

function ResultCard({ result, userInput, loading }) {
  const [displayText, setDisplayText] = useState("");
  const [dotVisible, setDotVisible] = useState(true);

  const timeoutRef = useRef(null);

  useEffect(() => {
    if (!result?.title) return;

    clearTimeout(timeoutRef.current);

    // Prepend "Book Name: " to the title
    const fullText = `Book Name: ${result.title}`;
    setDisplayText("");

    let i = 0;

    const typeWriter = () => {
      if (i < fullText.length) {
        setDisplayText(fullText.slice(0, i + 1));
        i++;
        timeoutRef.current = setTimeout(typeWriter, 100);
      }
    };

    typeWriter();

    return () => clearTimeout(timeoutRef.current);
  }, [result?.title]);

  // Pulsing dot while loading
  useEffect(() => {
    if (loading) {
      const interval = setInterval(() => setDotVisible((v) => !v), 500);
      return () => clearInterval(interval);
    }
  }, [loading]);

  if (!userInput && !loading && !result) return null;

  return (
    <div className="flex flex-col max-w-2xl mx-auto py-6 space-y-6 h-full overflow-hidden">
      {userInput && (
        <div className="flex justify-end">
          <div className="bg-gray-100 text-gray-800 rounded-2xl px-5 py-3 shadow-sm max-w-xs break-words">
            {userInput.file ? userInput.file.name : userInput.text}
          </div>
        </div>
      )}

      {loading && (
        <div className="flex items-start space-x-3">
          <div
            className={`w-4 h-4 bg-gray-800 rounded-full mt-3 transition-opacity duration-500 ${
              dotVisible ? "opacity-100" : "opacity-20"
            }`}
          ></div>
        </div>
      )}

      {result && (
        <div className="flex justify-start">
          <div className="bg-white border border-gray-200 text-gray-800 rounded-2xl px-5 py-3 shadow-sm max-w-md whitespace-pre-line">
            {displayText}
          </div>
        </div>
      )}
    </div>
  );
}

export default ResultCard;
