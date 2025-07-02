import React, { useState } from "react";
import { fetchIntention } from "../api/intention";

function IntentionForm() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = await fetchIntention(input);
    setResult(data);
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input value={input} onChange={e => setInput(e.target.value)} />
        <button type="submit">분석</button>
      </form>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}

export default IntentionForm;
