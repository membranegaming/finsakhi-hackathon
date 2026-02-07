import React from 'react';

const SceneBackground = ({ scene }) => {
    const sceneBackgrounds = {
        'village_home': { gradient: 'linear-gradient(to bottom, #87CEEB 0%, #F4A460 50%, #8B4513 100%)' },
        'market': { gradient: 'linear-gradient(135deg, #FF6B35 0%, #F7931E 50%, #FDC830 100%)' },
        'bank': { gradient: 'linear-gradient(to bottom, #E0E0E0 0%, #BDBDBD 50%, #9E9E9E 100%)' },
        'mentor_house': { gradient: 'linear-gradient(to bottom, #D7CCC8 0%, #A1887F 50%, #8D6E63 100%)' },
        'street': { gradient: 'linear-gradient(to bottom, #90CAF9 0%, #BCAAA4 50%, #757575 100%)' },
        'farm_field': { gradient: 'linear-gradient(to bottom, #81D4FA 0%, #AED581 40%, #9CCC65 100%)' },
        'irrigation': { gradient: 'linear-gradient(to bottom, #4FC3F7 0%, #66BB6A 50%, #558B2F 100%)' },
        'community_center': { gradient: 'linear-gradient(to bottom, #FFE082 0%, #FFB74D 50%, #F57C00 100%)' },
        'shop_interior': { gradient: 'linear-gradient(135deg, #FFF9C4 0%, #FFE082 50%, #FFB74D 100%)' },
        'shop_exterior': { gradient: 'linear-gradient(to bottom, #B3E5FC 0%, #FFE0B2 50%, #FFAB91 100%)' },
        'construction_site': { gradient: 'linear-gradient(to bottom, #90CAF9 0%, #FFCC80 40%, #A1887F 100%)' },
        'labor_chowk': { gradient: 'linear-gradient(135deg, #FFCCBC 0%, #BCAAA4 50%, #8D6E63 100%)' },
        'training_center': { gradient: 'linear-gradient(to bottom, #E1F5FE 0%, #B3E5FC 50%, #81D4FA 100%)' },
        'default': { gradient: 'linear-gradient(135deg, #FFF8E7 0%, #FFE4B5 50%, #F5DEB3 100%)' },
    };
    const current = sceneBackgrounds[scene] || sceneBackgrounds['default'];

    return (
        <div className="game-scene-background" style={{ background: current.gradient }}>
            <div className="game-scene-overlay"></div>
        </div>
    );
};

export default SceneBackground;
