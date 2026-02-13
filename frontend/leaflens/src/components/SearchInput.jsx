import { useRef, useState } from "react";
import { HiOutlinePhotograph, HiPaperAirplane } from "react-icons/hi";

function SearchInput({ onSearch, loading }) {
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const fileInputRef = useRef();

  const handleSubmit = () => {
    if (!text && !file) return;
    onSearch({ text, file });
    setText("");
    setFile(null);
  };

  const hasInput = text.length > 0 || file;

  return (
    <div className="w-full p-4 border-t border-gray-100 bg-white flex justify-center">
      <div
        className={`flex items-center w-full max-w-2xl border border-gray-300 rounded-full px-4 py-3 shadow-sm transition-colors ${
          loading ? "bg-gray-100" : "bg-white"
        }`}
      >

        <button
          onClick={() => fileInputRef.current.click()}
          disabled={loading}
          className="text-gray-500 mr-1 mt-1"
        >
          <HiOutlinePhotograph className="cursor-pointer hover:text-gray-600 text-2xl"/>
        </button>

        <input
          type="file"
          hidden
          ref={fileInputRef}
          onChange={(e) => setFile(e.target.files[0])}
        />

        <input
          type="text"
          value={text}
          disabled={loading}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type a sentence from the book..."
          className="flex-1 outline-none bg-transparent text-gray-700"
        />

        {hasInput && (
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="ml-3 mt-1 text-gray-600"
          >
            <HiPaperAirplane className="rotate-30 cursor-pointer hover:text-gray-700 text-2xl"/>
          </button>
        )}
      </div>
    </div>
  );
}

export default SearchInput;
