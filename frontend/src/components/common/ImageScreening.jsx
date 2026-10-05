import {useState} from 'react';
import {Button, Card, Field, Notice} from './UI';
import {predictImage, validateImage} from '../../services/imageService';

export default function ImageScreening({demo}) {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const select = event => {
    setResult(null); setError(''); setFile(null);
    const candidate = event.target.files?.[0];
    try { validateImage(candidate); setFile(candidate); } catch (e) { setError(e.message); }
  };
  const predict = async () => {
    setBusy(true); setError(''); setResult(null);
    try { setResult(await predictImage(file)); } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };
  return <Card title="Cattle image screening" subtitle="Independent Healthy / FMD / Lumpy screening. Image and symptom probabilities are not combined.">
    <div className="padded form-stack">
      <Field label="Cattle image" hint="JPEG, PNG or WebP, up to 10 MiB. Images are not permanently stored.">
        <input id="cattle-image" type="file" accept="image/jpeg,image/png,image/webp" onChange={select} disabled={busy}/>
      </Field>
      <Button onClick={predict} loading={busy} disabled={!file || busy}>Screen cattle image</Button>
      {error && <div role="alert"><Notice tone="danger">{error}</Notice></div>}
      {result && <div aria-live="polite">
        <p className="eyebrow">AI-ASSISTED SCREENING RESULT</p>
        <h3>{result.prediction.display_name}</h3>
        <p>Model confidence: {result.prediction.confidence_percent}% — this is not diagnostic certainty.</p>
        {result.prediction.low_confidence && <Notice>Low confidence: veterinary assessment recommended.</Notice>}
        <ul>{Object.entries(result.probabilities).map(([label, value]) => <li key={label}>{label}: {(value * 100).toFixed(2)}%</li>)}</ul>
        <p>{result.message}</p><Notice>{result.disclaimer}</Notice>
      </div>}
    </div>
  </Card>;
}
