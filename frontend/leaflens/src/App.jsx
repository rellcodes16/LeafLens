import { useEffect, useState } from "react";
import { Toaster, toast } from "react-hot-toast";
import SearchInput from "./components/SearchInput";
import ResultCard from "./components/ResultCard";
import Header from "./components/Header";
import InfoModal from "./components/InfoModal";
import { searchByImage, searchByText } from "./services/api";

function App() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    setShowInfo(true);
  }, []);

const handleSearch = async ({ text, file }) => {
  setHasSearched(true);

  const newEntry = {
    id: Date.now(),
    userInput: { text, file },
    result: null,
    loading: true,
  };

  setHistory((prev) => [...prev, newEntry]);

  try {
    setLoading(true);

    let response;
    if (file) {
      response = await searchByImage(file);
    } else {
      response = await searchByText(text);
    }

    if (response.status === "fail") {
      const msgMap = {
        "Not enough readable text":
          "Your search text or image is too short or unclear.",
        "No matches found":
          "No books matched your query. Try using more words or a different phrase.",
        "Non-English text":
          "Currently, only English text is supported for search.",
        "Low confidence":
          "We couldn’t confidently identify a book. Try a clearer image or more descriptive text.",
      };

      const userMessage = msgMap[response.reason] || response.reason;

      toast.error(userMessage);

      setHistory((prev) =>
        prev.map((item) =>
          item.id === newEntry.id
            ? { ...item, result: { status: "fail", reason: userMessage }, loading: false }
            : item
        )
      );

      return; 
    }
    setHistory((prev) =>
      prev.map((item) =>
        item.id === newEntry.id
          ? { ...item, result: response, loading: false }
          : item
      )
    );
  } catch (err) {
    console.error(err);

    let failMsg = "An unexpected error occurred. Please try again.";

    if (err.response) {
      const status = err.response.status;
      const data = err.response.data;

      if (status === 400) {
        failMsg =
          (data?.detail && Array.isArray(data.detail)
            ? data.detail.map((d) => d.msg).join(", ")
            : "Invalid search input. Please enter a proper query.") ||
          "Bad Request";
      } else if (status >= 500) {
        failMsg = "Server error. Please try again later.";
      } else {
        failMsg = data?.reason || `Error ${status}`;
      }
    } else if (err.request) {
      failMsg =
        "Network error: could not reach the server. Check your connection.";
    }

    toast.error(failMsg);

    setHistory((prev) =>
      prev.map((item) =>
        item.id === newEntry.id
          ? { ...item, result: { status: "fail", reason: failMsg }, loading: false }
          : item
      )
    );
  } finally {
    setLoading(false);
  }
};


  return (
    <div className="flex flex-col h-screen bg-white">
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 2000,
          style: {
            borderRadius: "12px",
            padding: "14px 18px",
            fontSize: "14px",
          },
        }}
      />

      <InfoModal isOpen={showInfo} onClose={() => setShowInfo(false)} />
      <Header />

      <div className="flex-1 overflow-y-auto px-4">
        {!hasSearched && !loading && (
          <div className="flex items-center justify-center h-full">
            <h2 className="text-5xl text-gray-600 font-semibold text-center">
              What book are you looking for?
            </h2>
          </div>
        )}

        {(hasSearched || loading) && (
          <ResultCard history={history} loading={loading} />
        )}
      </div>

      <SearchInput onSearch={handleSearch} loading={loading} />
    </div>
  );
}

export default App