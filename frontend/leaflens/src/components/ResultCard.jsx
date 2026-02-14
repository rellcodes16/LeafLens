import { useEffect, useRef, useState } from "react";

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

function ResultCard({ history }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const formatBookName = (rawName) => {
    if (!rawName) return "";

    rawName = rawName.replace(/\.txt$/i, "");
    rawName = rawName.replace(/[_-]+/g, " ");

    return rawName
      .toLowerCase()
      .split(" ")
      .filter(Boolean)
      .map((word) =>
        word.charAt(0).toUpperCase() + word.slice(1)
      )
      .join(" ");
  };

  return (
    <div className="flex flex-col max-w-2xl mx-auto py-6 space-y-6">

      {history.map((item) => {
        const bookName = formatBookName(
          item.result?.title || item.result?.book
        );

        return (
          <div key={item.id} className="space-y-4">

            <div className="flex justify-end">
              <div className="bg-gray-100 text-gray-800 rounded-2xl px-5 py-3 shadow-sm max-w-xs break-words">

                {item.userInput.file ? (
                  <img
                    src={URL.createObjectURL(item.userInput.file)}
                    alt="sent"
                    className="max-h-48 rounded-lg"
                  />
                ) : (
                  item.userInput.text
                )}

              </div>
            </div>

      <div className="flex justify-start">

      {item.loading ? (
        <div className="flex items-center space-x-2 px-2 py-2">
          <div className="w-4 h-4 bg-gray-800 rounded-full animate-pulse"></div>
        </div>
       ) : (
      <div className="bg-white border border-gray-200 text-gray-800 rounded-2xl px-5 py-3 shadow-sm max-w-md whitespace-pre-line">
        <TypewriterText text={`Book Name: ${bookName}`} />
      </div>
    )}

    </div>

          </div>
        );
      })}

      <div ref={bottomRef} />
    </div>
  );
}

export default ResultCard;
