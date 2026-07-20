import { useState, useEffect, useRef } from "react";
import {
  BookOpen,
  Download,
  Trash2,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import "./App.css";

type BookStatus =
  | "PENDING"
  | "GENERATING_OUTLINE"
  | "GENERATING_CHAPTERS"
  | "GENERATING_PDF"
  | "COMPLETED"
  | "FAILED";

interface BookChapter {
  id: number;
  book_id: number;
  chapter_number: number;
  title: string;
  content: string | null;
  generation_status: "PENDING" | "GENERATING" | "COMPLETED" | "FAILED";
  created_at: string;
}

interface Book {
  id: number;
  title: string;
  outline: string | null;
  status: BookStatus;
  total_chapters: number | null;
  generated_chapters: number;
  pdf_path: string | null;
  error_message: string | null;
  retry_count: number;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  chapters: BookChapter[];
}

function App() {
  const [books, setBooks] = useState<Book[]>([]);
  const [selectedBook, setSelectedBook] = useState<Book | null>(null);
  const [title, setTitle] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progressMessage, setProgressMessage] = useState("");
  const eventSourceRef = useRef<EventSource | null>(null);

  // Fetch all books on load
  const fetchBooks = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/books");
      const data = await res.json();
      setBooks(data);
    } catch (error) {
      console.error("Error fetching books:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBooks();
  }, []);

  const handleCreateBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    try {
      const res = await fetch("/api/books", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim() }),
      });
      const newBook = await res.json();
      setBooks([newBook, ...books]);
      setTitle("");
      startGeneration(newBook.id);
    } catch (error) {
      console.error("Error creating book:", error);
    }
  };

  const startGeneration = async (bookId: number) => {
    setIsGenerating(true);
    setSelectedBook(null);

    // Connect to SSE stream
    const eventSource = new EventSource(`/api/books/${bookId}/stream`);
    eventSourceRef.current = eventSource;

    eventSource.addEventListener("generation_started", () => {
      setProgressMessage("Generation started...");
    });

    eventSource.addEventListener("outline_started", () => {
      setProgressMessage("Generating outline...");
    });

    eventSource.addEventListener("outline_created", () => {
      setProgressMessage("Outline created, starting chapters...");
      fetchBooks();
    });

    eventSource.addEventListener("chapter_started", (e) => {
      const data = JSON.parse(e.data);
      setProgressMessage(
        `Generating Chapter ${data.chapter_number}: ${data.title}`,
      );
      fetchBooks();
    });

    eventSource.addEventListener("chapter_completed", (e) => {
      const data = JSON.parse(e.data);
      setProgressMessage(`Chapter ${data.chapter_number} completed!`);
      fetchBooks();
    });

    eventSource.addEventListener("pdf_generation_started", () => {
      setProgressMessage("Generating PDF...");
      fetchBooks();
    });

    eventSource.addEventListener("completed", () => {
      setProgressMessage("Book completed!");
      setIsGenerating(false);
      fetchBooks();
      eventSource.close();
    });

    eventSource.addEventListener("failed", (e) => {
      const data = JSON.parse(e.data);
      setProgressMessage(`Error: ${data.error}`);
      setIsGenerating(false);
      fetchBooks();
      eventSource.close();
    });

    eventSource.onerror = () => {
      console.error("SSE error");
      setIsGenerating(false);
      eventSource.close();
    };
  };

  const handleViewBook = async (book: Book) => {
    try {
      const res = await fetch(`/api/books/${book.id}`);
      const data = await res.json();
      setSelectedBook(data);
    } catch (error) {
      console.error("Error fetching book:", error);
    }
  };

  const handleDownload = (book: Book) => {
    window.open(`/api/books/${book.id}/download`, "_blank");
  };

  const handleDelete = async (bookId: number) => {
    if (!confirm("Are you sure you want to delete this book?")) return;
    try {
      await fetch(`/api/books/${bookId}`, { method: "DELETE" });
      setBooks(books.filter((b) => b.id !== bookId));
      if (selectedBook?.id === bookId) setSelectedBook(null);
    } catch (error) {
      console.error("Error deleting book:", error);
    }
  };

  const getStatusColor = (status: BookStatus) => {
    switch (status) {
      case "COMPLETED":
        return "text-green-600 bg-green-50";
      case "FAILED":
        return "text-red-600 bg-red-50";
      case "GENERATING_OUTLINE":
      case "GENERATING_CHAPTERS":
      case "GENERATING_PDF":
        return "text-blue-600 bg-blue-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getStatusIcon = (status: BookStatus) => {
    switch (status) {
      case "COMPLETED":
        return <CheckCircle2 className="w-4 h-4" />;
      case "FAILED":
        return <AlertCircle className="w-4 h-4" />;
      case "GENERATING_OUTLINE":
      case "GENERATING_CHAPTERS":
      case "GENERATING_PDF":
        return <Loader2 className="w-4 h-4 animate-spin" />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
            <BookOpen className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            AI Book Generator
          </h1>
          <p className="text-slate-600">
            Create professional books with AI-powered content generation
          </p>
        </div>

        {/* Create Book Form */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 mb-8">
          <form onSubmit={handleCreateBook} className="flex gap-4">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter book title..."
              className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isGenerating}
            />
            <button
              type="submit"
              disabled={isGenerating || !title.trim()}
              className="px-6 py-3 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isGenerating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : null}
              {isGenerating ? "Generating..." : "Generate Book"}
            </button>
          </form>
          {progressMessage && (
            <div className="mt-4 text-sm text-slate-600 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              {progressMessage}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Books List */}
          <div className="lg:col-span-1">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">
              Your Books
            </h2>
            {loading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
              </div>
            ) : books.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                No books yet. Create your first book above!
              </div>
            ) : (
              <div className="space-y-3">
                {books.map((book) => (
                  <div
                    key={book.id}
                    onClick={() => handleViewBook(book)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      selectedBook?.id === book.id
                        ? "border-blue-500 bg-blue-50"
                        : "border-slate-200 bg-white hover:border-slate-300"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-slate-900 truncate">
                          {book.title}
                        </h3>
                        <div className="flex items-center gap-2 mt-2">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(book.status)}`}
                          >
                            {getStatusIcon(book.status)}
                            {book.status.replace("_", " ")}
                          </span>
                          {book.total_chapters && (
                            <span className="text-xs text-slate-500">
                              {book.generated_chapters}/{book.total_chapters}{" "}
                              chapters
                            </span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(book.id);
                        }}
                        className="p-1 text-slate-400 hover:text-red-500 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Book Details */}
          <div className="lg:col-span-2">
            {selectedBook ? (
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="p-6 border-b border-slate-200">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-2xl font-bold text-slate-900">
                        {selectedBook.title}
                      </h2>
                      <div className="flex items-center gap-3 mt-2">
                        <span
                          className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedBook.status)}`}
                        >
                          {getStatusIcon(selectedBook.status)}
                          {selectedBook.status.replace("_", " ")}
                        </span>
                        {selectedBook.pdf_path && (
                          <button
                            onClick={() => handleDownload(selectedBook)}
                            className="inline-flex items-center gap-2 px-3 py-1 bg-green-600 text-white rounded-full text-sm font-medium hover:bg-green-700 transition-colors"
                          >
                            <Download className="w-4 h-4" />
                            Download PDF
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-6 max-h-[600px] overflow-y-auto">
                  {selectedBook.chapters.length > 0 ? (
                    <div className="space-y-6">
                      {selectedBook.chapters.map((chapter) => (
                        <div
                          key={chapter.id}
                          className="border-b border-slate-100 pb-6 last:border-0"
                        >
                          <div className="flex items-center gap-2 mb-3">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                                chapter.generation_status === "COMPLETED"
                                  ? "text-green-600 bg-green-50"
                                  : chapter.generation_status === "GENERATING"
                                    ? "text-blue-600 bg-blue-50"
                                    : "text-gray-600 bg-gray-50"
                              }`}
                            >
                              {chapter.generation_status === "COMPLETED" ? (
                                <CheckCircle2 className="w-3 h-3" />
                              ) : chapter.generation_status === "GENERATING" ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : null}
                              Chapter {chapter.chapter_number}
                            </span>
                            <h3 className="font-semibold text-slate-900">
                              {chapter.title}
                            </h3>
                          </div>
                          {chapter.content ? (
                            <div className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                              {chapter.content}
                            </div>
                          ) : (
                            <div className="text-slate-400 italic">
                              Content not yet generated...
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      No chapters yet.
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <BookOpen className="w-8 h-8 text-slate-400" />
                </div>
                <h3 className="text-lg font-medium text-slate-900 mb-2">
                  Select a book to view
                </h3>
                <p className="text-slate-500">
                  Choose a book from the list to see its details
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
