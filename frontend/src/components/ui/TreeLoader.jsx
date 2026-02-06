import './TreeLoader.css';

function TreeLoader({ message = "Loading..." }) {
  return (
    <div className="tree-loader-wrapper">
      <div className="tree-loader-container">
        {/* Tree SVG Animation */}
        <div className="tree-animation">
          <svg viewBox="0 0 100 120" className="tree-svg">
            {/* Tree trunk */}
            <rect 
              x="45" y="70" 
              width="10" height="30" 
              className="tree-trunk"
            />
            
            {/* Tree layers - bottom to top */}
            <polygon 
              points="50,10 20,45 80,45" 
              className="tree-layer tree-layer-1"
            />
            <polygon 
              points="50,25 25,55 75,55" 
              className="tree-layer tree-layer-2"
            />
            <polygon 
              points="50,40 30,70 70,70" 
              className="tree-layer tree-layer-3"
            />
            
            {/* Decorative circles (like fruits/ornaments) */}
            <circle cx="35" cy="50" r="3" className="tree-ornament ornament-1" />
            <circle cx="65" cy="50" r="3" className="tree-ornament ornament-2" />
            <circle cx="50" cy="35" r="3" className="tree-ornament ornament-3" />
            <circle cx="40" cy="62" r="2.5" className="tree-ornament ornament-4" />
            <circle cx="60" cy="62" r="2.5" className="tree-ornament ornament-5" />
          </svg>
          
          {/* Ground/grass */}
          <div className="tree-ground"></div>
        </div>
        
        {/* Loading text */}
        <p className="loader-message">{message}</p>
        
        {/* Loading dots */}
        <div className="loading-dots">
          <span className="dot"></span>
          <span className="dot"></span>
          <span className="dot"></span>
        </div>
      </div>
    </div>
  );
}

export default TreeLoader;

