import React, { useState } from 'react';

const PredictiveAccounting: React.FC = () => {
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch('http://localhost:8000/predictive-accounting', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, date }),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setResult({ error: 'Submission failed' });
    }
    setLoading(false);
  };

  return (
    <div className="page-container">
      <h2>Predictive Accounting</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Title:
            <input value={title} onChange={e => setTitle(e.target.value)} required />
          </label>
        </div>
        <div>
          <label>Date:
            <input type="date" value={date} onChange={e => setDate(e.target.value)} required />
          </label>
        </div>
        <button type="submit" disabled={loading}>{loading ? 'Submitting...' : 'Submit'}</button>
      </form>
      {result && (
        <pre style={{ marginTop: 20 }}>{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
};

export default PredictiveAccounting;
