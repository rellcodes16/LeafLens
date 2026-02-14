import { useRef, useState } from "react";
import { HiOutlinePhotograph, HiPaperAirplane, HiX } from "react-icons/hi";

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

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    setFile(selectedFile);
    setText(""); 
  };

  const removeImage = () => {
    setFile(null);
    fileInputRef.current.value = ""; 
  };

  const hasInput = text.length > 0 || file;

  return (
    <div className="w-full border-t border-gray-100 bg-white flex justify-center">
      <div className="w-full max-w-2xl p-4 space-y-2">
        {file && (
          <div className="relative w-fit">
            <img
              src={URL.createObjectURL(file)}
              alt="preview"
              className="h-20 rounded-lg border border-gray-200 shadow-sm"
            />

            <button
              onClick={removeImage}
              className="absolute -top-2 -right-2 bg-white border border-gray-300 rounded-full p-1 shadow hover:bg-gray-100"
            >
              <HiX className="text-gray-600 text-sm" />
            </button>
          </div>
        )}
        <div
          className={`flex items-center w-full border border-gray-300 rounded-full px-4 py-3 shadow-sm transition-colors ${
            loading ? "bg-gray-100" : "bg-white"
          }`}
        >
          <button
            onClick={() => fileInputRef.current.click()}
            disabled={loading || file} 
            className={`mr-2 ${
              file ? "text-gray-300" : "text-gray-500 hover:text-gray-600"
            }`}
          >
            <HiOutlinePhotograph className="text-2xl" />
          </button>

          <input
            type="file"
            hidden
            ref={fileInputRef}
            accept="image/*"
            onChange={handleFileChange}
          />
          <input
            type="text"
            value={text}
            disabled={loading || file} 
            onChange={(e) => setText(e.target.value)}
            placeholder={
              file
                ? "Remove image to type..."
                : "Type a sentence from the book..."
            }
            className="flex-1 outline-none bg-transparent text-gray-700 disabled:text-gray-400"
          />
          {hasInput && (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="ml-3 text-gray-600 hover:text-gray-700"
            >
              <HiPaperAirplane className="rotate-45 text-2xl" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default SearchInput;
