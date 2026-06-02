import React, { useState, useRef, useEffect, useCallback } from 'react';
import './App.css';

const BOOKS = {
  "Old Testament": [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles",
    "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah",
    "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah",
    "Haggai", "Zechariah", "Malachi"
  ],
  "New Testament": [
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
    "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews",
    "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
    "Jude", "Revelation"
  ]
};

const CHAPTER_COUNTS = {
  "Genesis": 50, "Exodus": 40, "Leviticus": 27, "Numbers": 36,
  "Deuteronomy": 34, "Joshua": 24, "Judges": 21, "Ruth": 4,
  "1 Samuel": 31, "2 Samuel": 24, "1 Kings": 22, "2 Kings": 25,
  "1 Chronicles": 29, "2 Chronicles": 36, "Ezra": 10, "Nehemiah": 13,
  "Esther": 10, "Job": 42, "Psalms": 150, "Proverbs": 31,
  "Ecclesiastes": 12, "Song of Solomon": 8, "Isaiah": 66,
  "Jeremiah": 52, "Lamentations": 5, "Ezekiel": 48, "Daniel": 12,
  "Hosea": 14, "Joel": 3, "Amos": 9, "Obadiah": 1, "Jonah": 4,
  "Micah": 7, "Nahum": 3, "Habakkuk": 3, "Zephaniah": 3,
  "Haggai": 2, "Zechariah": 14, "Malachi": 4, "Matthew": 28,
  "Mark": 16, "Luke": 24, "John": 21, "Acts": 28, "Romans": 16,
  "1 Corinthians": 16, "2 Corinthians": 13, "Galatians": 6,
  "Ephesians": 6, "Philippians": 4, "Colossians": 4,
  "1 Thessalonians": 5, "2 Thessalonians": 3, "1 Timothy": 6,
  "2 Timothy": 4, "Titus": 3, "Philemon": 1, "Hebrews": 13,
  "James": 5, "1 Peter": 5, "2 Peter": 3, "1 John": 5,
  "2 John": 1, "3 John": 1, "Jude": 1, "Revelation": 22
};

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [selectedVerse, setSelectedVerse] = useState(null);
  const [crossRefs, setCrossRefs] = useState([]);
  const [expandedRef, setExpandedRef] = useState(null);
  const [loading, setLoading] = useState(false);
  const [refLoading, setRefLoading] = useState(false);
  const [mode, setMode] = useState('home');
  const [selectedBook, setSelectedBook] = useState(null);
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [chapterVerses, setChapterVerses] = useState([]);
  const [chapterLoading, setChapterLoading] = useState(false);
  const [keywords, setKeywords] = useState([]);
  const [assistantQuery, setAssistantQuery] = useState('');
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [leftWidth, setLeftWidth] = useState(60);
  const isDragging = useRef(false);
  const containerRef = useRef(null);
  const conversationEndRef = useRef(null);
  const API_BASE = "https://bible-study-backend-m0b6.onrender.com";

  useEffect(() => {
    if (conversationEndRef.current) {
      conversationEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversation]);

  const handleMouseDown = () => { isDragging.current = true; };

  const handleMouseMove = useCallback((e) => {
    if (!isDragging.current || !containerRef.current) return;
    const container = containerRef.current.getBoundingClientRect();
    const newLeft = ((e.clientX - container.left) / container.width) * 100;
    if (newLeft >= 25 && newLeft <= 75) setLeftWidth(newLeft);
  }, []);

  const handleMouseUp = () => { isDragging.current = false; };

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove]);

  const handleSearch = async () => {
    if (!query.trim()) return;
    const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
    const data = await response.json();
    setResults(data);
    setSelectedVerse(null);
    setCrossRefs([]);
    setExpandedRef(null);
    setMode('search');
  };

  const handleBookClick = (book) => {
    setSelectedBook(book);
    setSelectedChapter(null);
    setChapterVerses([]);
    setResults(null);
    setSelectedVerse(null);
    setCrossRefs([]);
    setMode('book');
  };

  const handleChapterClick = async (chapter, book = null) => {
    const bookName = book || selectedBook;
    setSelectedBook(bookName);
    setSelectedChapter(chapter);
    setChapterLoading(true);
    setSelectedVerse(null);
    setCrossRefs([]);
    setMode('read');
    const response = await fetch(`${API_BASE}/passage?q=${encodeURIComponent(`${bookName} ${chapter}`)}`);
    const data = await response.json();
    const lines = data.text.split(/(?=\[\d+\])/).filter(line => line.trim());
    const parsed = lines.map((line, i) => {
      const match = line.match(/^\[(\d+)\]\s*/);
      const verseNum = match ? parseInt(match[1]) : i + 1;
      const text = line.replace(/^\[\d+\]\s*/, '').trim();
      return { reference: `${bookName} ${chapter}:${verseNum}`, text };
    });
    setChapterVerses(parsed);
    setChapterLoading(false);
  };

  const handleVerseClick = async (verse) => {
    setSelectedVerse(verse);
    setExpandedRef(null);
    setLoading(true);
    setKeywords([]);
    const [crossResponse, keywordsResponse] = await Promise.all([
      fetch(`${API_BASE}/crossreferences?q=${encodeURIComponent(verse.reference)}`),
      fetch(`${API_BASE}/keywords?reference=${encodeURIComponent(verse.reference)}`)
    ]);
    const crossData = await crossResponse.json();
    const keywordsData = await keywordsResponse.json();
    setCrossRefs(crossData.cross_references || []);
    setKeywords(keywordsData.keywords || []);
    setLoading(false);
  };

  const handleCrossRefClick = async (ref) => {
    if (expandedRef?.reference === ref.reference) {
      setExpandedRef(null);
      return;
    }
    setRefLoading(ref.reference);
    const response = await fetch(`${API_BASE}/passage?q=${encodeURIComponent(ref.reference)}`);
    const data = await response.json();
    setExpandedRef({ reference: ref.reference, text: data.text });
    setRefLoading(false);
  };

  const handleAssistantQuery = async () => {
    if (!assistantQuery.trim()) return;
    const userMessage = assistantQuery;
    setAssistantQuery('');
    setConversation(prev => [...prev, { role: 'user', content: userMessage }]);
    setAssistantLoading(true);
    const verseParam = selectedVerse ? `&verse=${encodeURIComponent(selectedVerse.reference)}` : '';
    const response = await fetch(`${API_BASE}/assistant?q=${encodeURIComponent(userMessage)}${verseParam}`);
    const data = await response.json();
    setConversation(prev => [...prev, { role: 'assistant', content: data.response }]);
    setAssistantLoading(false);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Bible Study</h1>
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search by passage or topic..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch}>Search</button>
        </div>
      </header>

      <div className="panels" ref={containerRef}>
        <div className="left-panel" style={{ width: `${leftWidth}%` }}>

          {mode === 'home' && (
            <div className="table-of-contents">
              {Object.entries(BOOKS).map(([testament, books]) => (
                <div key={testament} className="testament-section">
                  <h2 className="testament-title">{testament}</h2>
                  <div className="books-grid">
                    {books.map(book => (
                      <div key={book} className="book-item" onClick={() => handleBookClick(book)}>
                        {book}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {mode === 'book' && selectedBook && (
            <div className="chapter-select">
              <div className="breadcrumb">
                <span className="breadcrumb-link" onClick={() => setMode('home')}>Bible</span>
                <span> › </span>
                <span>{selectedBook}</span>
              </div>
              <h2 className="book-title">{selectedBook}</h2>
              <p className="chapter-label">Select a chapter</p>
              <div className="chapters-grid">
                {Array.from({ length: CHAPTER_COUNTS[selectedBook] }, (_, i) => i + 1).map(ch => (
                  <div key={ch} className="chapter-item" onClick={() => handleChapterClick(ch)}>{ch}</div>
                ))}
              </div>
            </div>
          )}

          {mode === 'read' && (
            <div className="chapter-view">
              <div className="breadcrumb">
                <span className="breadcrumb-link" onClick={() => setMode('home')}>Bible</span>
                <span> › </span>
                <span className="breadcrumb-link" onClick={() => setMode('book')}>{selectedBook}</span>
                <span> › </span>
                <span>Chapter {selectedChapter}</span>
              </div>
              <h2 className="chapter-title">{selectedBook} {selectedChapter}</h2>
              {chapterLoading && <p className="placeholder">Loading...</p>}
              {!chapterLoading && chapterVerses.map((verse, i) => (
                <p
                  key={i}
                  className={`verse-line ${selectedVerse?.reference === verse.reference ? 'verse-line-selected' : ''}`}
                  onClick={() => handleVerseClick(verse)}
                >
                  <span className="verse-number">{i + 1}</span>
                  {verse.text}
                </p>
              ))}
              <div className="chapter-nav">
                <button onClick={() => selectedChapter > 1 && handleChapterClick(selectedChapter - 1)} disabled={selectedChapter <= 1}>← Previous</button>
                <span>{selectedBook} {selectedChapter}</span>
                <button onClick={() => selectedChapter < CHAPTER_COUNTS[selectedBook] && handleChapterClick(selectedChapter + 1)} disabled={selectedChapter >= CHAPTER_COUNTS[selectedBook]}>Next →</button>
              </div>
            </div>
          )}

          {mode === 'search' && results && (
            <div className="results">
              <div className="breadcrumb">
                <span className="breadcrumb-link" onClick={() => { setResults(null); setMode('home'); }}>Bible</span>
                <span> › Search results</span>
              </div>
              <h2 className="results-title">Results for "{results.query}"</h2>
              {results.results.map((verse, i) => (
                <div
                  key={i}
                  className={`verse-card ${selectedVerse?.reference === verse.reference ? 'selected' : ''}`}
                  onClick={() => handleVerseClick(verse)}
                >
                  <div className="verse-card-header">
                    <h3>{verse.reference}</h3>
                    <button
                      className="goto-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        const ref = verse.reference.replace(/–/g, '-').replace(/—/g, '-');
                        const chapterMatch = ref.match(/^(.*)\s(\d+)(?::\d+(?:-\d+)?)?$/);
                        if (chapterMatch) handleChapterClick(parseInt(chapterMatch[2]), chapterMatch[1]);
                      }}
                    >
                      Read chapter →
                    </button>
                  </div>
                  <p>{verse.text}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="divider" onMouseDown={handleMouseDown} />

        <div className="right-panel" style={{ width: `${100 - leftWidth}%` }}>
          {selectedVerse && (
            <div>
              <div className="selected-verse">
                <h2>{selectedVerse.reference}</h2>
                <p>{selectedVerse.text}</p>
              </div>

              {keywords.length > 0 && (
                <div className="section">
                  <h3>Key Words</h3>
                  {keywords.map((kw, i) => (
                    <div key={i} className="keyword-item">
                      <div className="keyword-header">
                        <span className="keyword-word">{kw.word}</span>
                        <span className="keyword-lemma">{kw.lemma}</span>
                        <span className="keyword-translit">{kw.transliteration}</span>
                      </div>
                      <p className="keyword-definition">{kw.definition}</p>
                    </div>
                  ))}
                </div>
              )}

              <div className="section">
                <h3>Cross References</h3>
                {loading && <p className="placeholder">Loading...</p>}
                {!loading && crossRefs.map((ref, i) => (
                  <div key={i}>
                    <div className="cross-ref-item" onClick={() => handleCrossRefClick(ref)}>
                      <span className="ref-name">{ref.reference}</span>
                      <span className="ref-votes">{ref.votes} connections</span>
                    </div>
                    {expandedRef?.reference === ref.reference && (
                      <div className="expanded-ref">
                        {refLoading === ref.reference ? <p className="placeholder">Loading...</p> : <p>{expandedRef.text}</p>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {!selectedVerse && (
            <p className="placeholder">Select a verse to see cross references and original language keywords.</p>
          )}

          <div className="assistant-section">
            <div className="assistant-header">
              <div className="assistant-icon">✦</div>
              <div>
                <h3>Study Assistant</h3>
                <p>Ask anything about this verse or any biblical topic</p>
              </div>
            </div>

            <div className="conversation">
              {conversation.length === 0 && (
                <p className="conversation-placeholder">Your study conversation will appear here.</p>
              )}
              {conversation.map((msg, i) => (
                <div key={i} className={`message message-${msg.role}`}>
                  <div className="message-label">{msg.role === 'user' ? 'You' : 'Assistant'}</div>
                  <p>{msg.content}</p>
                </div>
              ))}
              {assistantLoading && (
                <div className="message message-assistant">
                  <div className="message-label">Assistant</div>
                  <div className="assistant-loading">
                    <div className="loading-dots">
                      <span></span><span></span><span></span>
                    </div>
                    <p>Searching sources...</p>
                  </div>
                </div>
              )}
              <div ref={conversationEndRef} />
            </div>

            <div className="assistant-input">
              <input
                type="text"
                placeholder="Ask a question..."
                value={assistantQuery}
                onChange={(e) => setAssistantQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAssistantQuery()}
              />
              <button onClick={handleAssistantQuery}>→</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;