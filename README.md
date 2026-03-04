**LeafLens**
LeafLens is a modern, AI-powered book recognition platform. It helps users quickly identify books from images of pages and text paragraphs snippets, making reading and research faster and easier.
With LeafLens, you can take a photo of a book page, and the platform will recognize the book, providing relevant details instantly.

**Features**
User Features
* Book Recognition – Identify books from typed texts and images of their pages in seconds.
* Book Details – Access titles and authors.
* Search & Explore – Quickly find books already in the database.

Admin Features
* Manage Books – Add, update, or remove book entries in the system.
* Monitor Usage – Track book recognition activity and popular books.
* Database Management – Keep book data organized and up to date.

**How It Works**
LeafLens combines several AI and data techniques to provide accurate book recognition:
* OCR (Optical Character Recognition) – Reads text from typed texts snippets and images of book pages. This allows the system to “see” the words just like a human would.
* Embeddings & Fingerprints – Text from the page is converted into unique digital representations, or “fingerprints,” using AI models like MPNet and MiniLM. These fingerprints capture the meaning of the text, not just the exact words.
* Similarity Matching – The system compares these fingerprints against a database of all stored books to find the closest match.
* SQL Database – Stores book details, metadata, and embeddings efficiently, enabling fast searches and organized book records.
By combining these technologies, LeafLens can recognize books even from partial pages or small snippets of text.

**System Highlights**
* AI-powered text recognition from images and texts.
* Fast search and matching using advanced algorithms.
* Scalable system designed to handle growing book collections.
* Easy-to-use interface for users.

**Tech Stack**
* Frontend: Web interface built with React and Tailwind, providing a modern, easy-to-use experience for users and admins.
* Backend: AI and search-powered server logic built with Python, handling book recognition, matching, and data management.
* Database: SQL database storing book details, metadata, and AI-generated embeddings for fast and organized search.
