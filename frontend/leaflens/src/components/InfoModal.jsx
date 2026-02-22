import { useEffect } from "react"
import { HiX } from "react-icons/hi"

function InfoModal({ isOpen, onClose }) {
  useEffect(() => {
    if (!isOpen) return

    const timer = setTimeout(() => {
      onClose()
    }, 20000)

    return () => clearTimeout(timer)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white w-[90%] max-w-md rounded-2xl shadow-xl p-6 relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600"
        >
          <HiX className="text-xl" />
        </button>

        <h2 className="text-lg text-center font-semibold text-gray-800 mb-3">
          Hiiiii, Just so you know 👋
        </h2>

        <p className="text-gray-600 text-sm leading-relaxed">
          This is a personal project with a limited book database.
          If your book isn’t found, it may not be included yet.
        </p>
      </div>
    </div>
  );
}

export default InfoModal;
