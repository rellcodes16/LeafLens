import { useEffect, useRef } from "react";
import TypewriterText from "./TypewriterText";

function ResultCard({ history }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const formatBookName = (rawName) => {
    if (!rawName) return "";
    rawName = rawName.replace(/\.txt$/i, "").trim();
    rawName = rawName.replace(/\(\d+\)$/, "").trim();
    rawName = rawName.replace(/[_-]+/g, " ");
    rawName = rawName.replace(/\s+\d+$/, "");
    return rawName
      .toLowerCase()
      .split(" ")
      .filter(Boolean)
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const formatAuthor = (author) => {
    if (!author) return "Unknown";
    const parts = author.split(",").map((p) => p.trim()).filter(Boolean);
    const capitalize = (str) =>
      str
        .split(" ")
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(" ");

    if (parts.length === 1) return capitalize(parts[0]);
    if (parts.length === 2) return `${capitalize(parts[0])} ${capitalize(parts[1])}`;
    if (parts.length === 3) return `${capitalize(parts[2])} ${capitalize(parts[1])} ${capitalize(parts[0])}`;
    if (parts.length === 4) {
      const first = `${capitalize(parts[0])} ${capitalize(parts[1])}`;
      const second = `${capitalize(parts[2])} ${capitalize(parts[3])}`;
      return `${first} and ${second}`;
    }
    if (parts.length === 2 && parts[0].toLowerCase() === "louisa may") return "Louisa May and Alcott";
    return capitalize(author.replace(/,/g, " "));
  };

  return (
    <div className="flex flex-col max-w-2xl mx-auto py-6 space-y-6">
      {history.map((item) => {
        console.log(item)
        const isError = item.result?.status === "fail";

        const bookName = isError ? null : formatBookName(item.result?.title || item.result?.book);
        const authorName = isError ? null : formatAuthor(item.result?.author);

        return (
          <div key={item.id} className="space-y-4">
            {/* User input */}
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
                <div
                  className={`bg-white border text-gray-800 rounded-2xl px-5 py-3 shadow-sm max-w-md whitespace-pre-line ${
                    isError ? "border-red-400 text-red-700" : "border-gray-200"
                  }`}
                >
                  <TypewriterText
                    text={
                      isError
                        ? item.result?.reason || "Unknown error occurred"
                        : `Book Name: ${bookName}\nAuthor: ${authorName}`
                    }
                  />
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
