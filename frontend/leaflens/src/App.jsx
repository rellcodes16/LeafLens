import { useState } from "react";
import Header from "./components/Header";
import SearchInput from "./components/SearchInput";
import ResultCard from "./components/ResultCard";
import { searchByText, searchByImage } from "./services/api";

function App() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

const handleSearch = async ({ text, file }) => {
  setHasSearched(true);

  const newEntry = {
    id: Date.now(),
    userInput: { text, file },
    result: null,      // result not ready yet
    loading: true,     // mark this entry as loading
  };

  // 1️⃣ Immediately add user message
  setHistory((prev) => [...prev, newEntry]);

  try {
    setLoading(true);

    let response;
    if (file) {
      response = await searchByImage(file);
    } else {
      response = await searchByText(text);
    }

    // 2️⃣ When API returns, update that specific entry
    setHistory((prev) =>
      prev.map((item) =>
        item.id === newEntry.id
          ? { ...item, result: response, loading: false }
          : item
      )
    );

  } catch (err) {
    console.error(err);
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="flex flex-col h-screen bg-white">
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

export default App;
