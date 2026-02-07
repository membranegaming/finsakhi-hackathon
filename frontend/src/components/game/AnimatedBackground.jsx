import React from 'react';

const AnimatedBackground = ({ scene }) => {
    const renderVillageHome = () => (
        <svg className="animated-bg" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice">
            <rect width="800" height="600" fill="url(#skyGradient)"/>
            <defs>
                <linearGradient id="skyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#87CEEB"/><stop offset="100%" stopColor="#E0F6FF"/>
                </linearGradient>
            </defs>
            <circle className="sun" cx="700" cy="100" r="50" fill="#FFD700"/>
            <ellipse className="cloud cloud1" cx="150" cy="80" rx="40" ry="20" fill="#FFF" opacity="0.8"/>
            <ellipse className="cloud cloud1" cx="170" cy="85" rx="50" ry="25" fill="#FFF" opacity="0.8"/>
            <ellipse className="cloud cloud2" cx="500" cy="120" rx="45" ry="22" fill="#FFF" opacity="0.7"/>
            <polygon points="0,400 200,250 400,400" fill="#8B7355" opacity="0.6"/>
            <polygon points="300,400 500,200 700,400" fill="#A0826D" opacity="0.5"/>
            <g className="tree tree1">
                <rect x="100" y="350" width="20" height="80" fill="#8B4513"/>
                <polygon points="110,350 70,380 150,380" fill="#228B22"/>
                <polygon points="110,330 80,360 140,360" fill="#32CD32"/>
                <polygon points="110,310 90,340 130,340" fill="#3CB371"/>
            </g>
            <g className="tree tree2">
                <rect x="650" y="360" width="18" height="70" fill="#8B4513"/>
                <polygon points="659,360 625,385 693,385" fill="#228B22"/>
                <polygon points="659,345 635,370 683,370" fill="#32CD32"/>
            </g>
            <rect x="300" y="320" width="200" height="150" fill="#D2691E"/>
            <polygon points="300,320 400,250 500,320" fill="#8B4513"/>
            <rect x="360" y="380" width="50" height="90" fill="#654321"/>
            <rect x="430" y="350" width="40" height="40" fill="#87CEEB"/>
            <rect y="470" width="800" height="130" fill="#90EE90"/>
        </svg>
    );

    const renderBank = () => (
        <svg className="animated-bg" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice">
            <rect width="800" height="600" fill="url(#citySky)"/>
            <defs>
                <linearGradient id="citySky" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#B0C4DE"/><stop offset="100%" stopColor="#E8F4F8"/>
                </linearGradient>
            </defs>
            <rect x="0" y="200" width="150" height="250" fill="#708090" opacity="0.4"/>
            <rect x="160" y="150" width="120" height="300" fill="#778899" opacity="0.4"/>
            <rect x="600" y="180" width="200" height="270" fill="#696969" opacity="0.4"/>
            <rect x="250" y="150" width="300" height="320" fill="#D3D3D3"/>
            <rect x="250" y="150" width="300" height="30" fill="#A9A9A9"/>
            {[0,1,2,3,4].map(row => [0,1,2,3,4].map(col => (
                <rect key={`w-${row}-${col}`} x={280+col*50} y={200+row*50} width="30" height="35" fill="#4682B4" opacity="0.7"/>
            )))}
            <rect x="370" y="400" width="60" height="70" fill="#654321"/>
            <rect y="470" width="800" height="130" fill="#696969"/>
            {[0,1,2,3,4].map(i => (
                <rect key={`rl-${i}`} className={`road-line line${i+1}`} x={i*150} y="530" width="100" height="8" fill="#FFD700"/>
            ))}
            <g className="car car1">
                <rect x="50" y="490" width="80" height="40" rx="5" fill="#FF4500"/>
                <rect x="60" y="475" width="60" height="25" rx="3" fill="#FF6347"/>
                <circle cx="70" cy="530" r="12" fill="#2F4F4F"/><circle cx="120" cy="530" r="12" fill="#2F4F4F"/>
            </g>
        </svg>
    );

    const renderFarmField = () => (
        <svg className="animated-bg" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice">
            <rect width="800" height="600" fill="url(#farmSky)"/>
            <defs>
                <linearGradient id="farmSky" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#87CEEB"/><stop offset="100%" stopColor="#B0E0E6"/>
                </linearGradient>
            </defs>
            <circle className="sun" cx="650" cy="80" r="45" fill="#FFD700"/>
            <polygon points="0,350 300,200 600,350" fill="#A0826D" opacity="0.3"/>
            {[0,1,2,3,4,5,6].map(i => (
                <rect key={`c-${i}`} className={`crop-row row${i}`} x={50+i*100} y={400+i*10} width="80" height="150" fill="#9ACD32" opacity="0.8"/>
            ))}
            <g className="tree tree1">
                <rect x="700" y="320" width="25" height="100" fill="#8B4513"/>
                <polygon points="712,320 670,360 754,360" fill="#228B22"/>
                <polygon points="712,295 680,335 744,335" fill="#32CD32"/>
            </g>
            <rect y="500" width="800" height="100" fill="#8B7355"/>
        </svg>
    );

    const renderConstructionSite = () => (
        <svg className="animated-bg" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice">
            <rect width="800" height="600" fill="url(#constSky)"/>
            <defs>
                <linearGradient id="constSky" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#90CAF9"/><stop offset="100%" stopColor="#FFCC80"/>
                </linearGradient>
            </defs>
            <rect x="200" y="200" width="250" height="250" fill="#A1887F" opacity="0.8"/>
            <rect x="100" y="180" width="60" height="270" fill="#795548"/>
            <line x1="130" y1="180" x2="300" y2="220" stroke="#FFB74D" strokeWidth="3"/>
            <rect x="500" y="300" width="180" height="150" fill="#BCAAA4"/>
            <rect y="450" width="800" height="150" fill="#A1887F"/>
        </svg>
    );

    const renderShop = () => (
        <svg className="animated-bg" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice">
            <rect width="800" height="600" fill="url(#shopSky)"/>
            <defs>
                <linearGradient id="shopSky" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#FFF9C4"/><stop offset="100%" stopColor="#FFE082"/>
                </linearGradient>
            </defs>
            <rect x="150" y="200" width="500" height="270" fill="#FFE0B2" stroke="#F57C00" strokeWidth="3"/>
            <rect x="150" y="180" width="500" height="30" fill="#F57C00"/>
            <rect x="350" y="380" width="80" height="90" fill="#8D6E63"/>
            <rect x="200" y="280" width="100" height="80" fill="#87CEEB" opacity="0.5"/>
            <rect x="500" y="280" width="100" height="80" fill="#87CEEB" opacity="0.5"/>
            <rect y="470" width="800" height="130" fill="#E8E8E8"/>
        </svg>
    );

    const renderScene = () => {
        switch(scene) {
            case 'village_home': case 'mentor_house': return renderVillageHome();
            case 'bank': case 'street': return renderBank();
            case 'farm_field': case 'irrigation': return renderFarmField();
            case 'construction_site': case 'labor_chowk': case 'training_center': return renderConstructionSite();
            case 'shop_interior': case 'shop_exterior': case 'warehouse': return renderShop();
            default: return renderVillageHome();
        }
    };

    return <div className="game-animated-background-container">{renderScene()}</div>;
};

export default AnimatedBackground;
