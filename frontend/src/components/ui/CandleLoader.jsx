import './CandleLoader.css';

export default function CandleLoader({ message, fullscreen = false }) {
  return (
    <div className={`candle-loader-wrapper${fullscreen ? ' fullscreen' : ''}`}>
      <div className="candle-loader">
        <div className="candle candle-green">
          <div className="wick"></div>
          <div className="body"></div>
          <div className="wick"></div>
        </div>
        <div className="candle candle-red">
          <div className="wick"></div>
          <div className="body"></div>
          <div className="wick"></div>
        </div>
        <div className="candle candle-green-2">
          <div className="wick"></div>
          <div className="body"></div>
          <div className="wick"></div>
        </div>
      </div>
      {message && <p className="candle-loader-text">{message}</p>}
    </div>
  );
}
