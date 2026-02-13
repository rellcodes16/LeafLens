import { useState } from "react";
import Header from "./components/Header";
import SearchInput from "./components/SearchInput";
import ResultCard from "./components/ResultCard";
import { searchByText, searchByImage } from "./services/api";

function App() {
  const [result, setResult] = useState(null);
  const [userInput, setUserInput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

const handleSearch = async ({ text, file }) => {
  try {
    setLoading(true);
    setHasSearched(true);

    setUserInput({ text, file });

    let response;
    if (file) {
      response = await searchByImage(file);
    } else {
      response = await searchByText(text);
    }

    setResult(response); 
  } catch (err) {
    console.error(err);
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="flex flex-col h-screen bg-white">
      <Header />

      <div className="flex-1 overflow-hidden px-4">
        {!hasSearched && !loading && (
          <div className="flex items-center justify-center h-full">
            <h2 className="text-5xl text-gray-600 font-semibold text-center">
              What book are you looking for?
            </h2>
          </div>
        )}

        {(hasSearched || loading) && (
          <ResultCard
            result={result}
            userInput={userInput}
            loading={loading}
          />
        )}
      </div>

      <SearchInput onSearch={handleSearch} loading={loading} />
    </div>
  );
}

export default App;
