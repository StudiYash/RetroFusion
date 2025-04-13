# ![Bounceario](https://github.com/StudiYash/RetroFusion/blob/main/Project%20Games/Sub-Project%2001%20-%20Bounceario/Bounceario%20Logo.png)

## Project Introduction 🛡️

### Abstract
**Bounceario** is a vibrant, retro-style 2D platformer built using **Pygame** and **Tkinter**. The game features a dynamic terrain system, randomly generated floating platforms, and various enemies like spiders that challenge the player’s reflexes. Players control a red bouncing ball with intuitive jump physics, collectible coins, and power-ups like mushrooms for temporary invincibility and guns for shooting bullets. Bounceario also includes background music, animated splash screens, and a heart-based life system, making it a polished and immersive mini-game experience designed for non-commercial creative learning.

### Project Timeline 

- **Start Date**: 2nd April 2025  
- **End Date**: 12th April 2025
- **Total Time Required**: 11 Days

### Developers Introduction  

| Name                   | GitHub Profile | LinkedIn Profile |
|------------------------|----------------|------------------|
| **Yash Suhas Shukla**  | [GitHub](https://github.com/StudiYash) | [LinkedIn](https://www.linkedin.com/in/yash-shukla-2024aiguy/) |

---

## Methodology 🚀

### Overview 🎮

Bounceario is built with a modular design, dividing responsibilities between various subsystems to create a rich, retro-style 2D platformer experience. The game leverages both **Tkinter** and **Pygame**—with Tkinter handling the splash screen and initial user interaction, and Pygame powering the main game loop, physics, rendering, and audio. This section outlines the complete game structure, providing insight into its architecture, core components, and overall functionality.

### Core Components 🔧

#### 1. Splash Screen & Initialization 🎨
- **Tkinter Splash Screen:**
  - Displays the game’s logo and two interactive buttons: **"Play"** and **"Controls"**.
  - Provides initial instructions and serves as a gateway to the main gameplay.
- **Transition to Gameplay:**
  - When the **"Play"** button is pressed, the splash screen is closed and control is handed off to the Pygame engine.

#### 2. Game Engine & Main Loop (Pygame) 🔄
- **State Management:**
  Bounceario uses a state machine to handle the different phases of gameplay:
  - **Start:** Waiting for user input to begin.
  - **Playing:** Main gameplay state with active physics, rendering, and input handling.
  - **Paused:** Temporarily suspends game activity while maintaining active timers (e.g., for power-ups).
  - **Respawn/Dying:** Manages transitions when the player loses a life or meets fatal collision conditions.
  - **Game Over:** Displays game over information and options to restart.
- **Event Handling:**
  - Processes user input (keyboard events for movement, jumping, shooting, pausing, etc.).
  - Listens for window events such as resizing.
  - Schedules custom events (e.g., background music transitions).

#### 3. Gameplay Mechanics & Physics ⚙️
- **Player Control (The Ball):**
  - Implements nuanced movement with physics-driven jumping (variable jump height via a bounce multiplier) and smooth horizontal motion.
  - Includes rotation animations and collision detection using Pygame masks.
- **Dynamic Terrain & Platforms:**
  - **Ground Manager:**
    - Generates a dynamic terrain using random points and linear interpolation to create smooth curves.
  - **Floating Platforms:**
    - Randomly generated above the ground to provide varying challenges and opportunities for coin or power-up spawns.
- **Obstacles & Power-Ups:**
  - **Obstacles:**
    - Static (ground/platform-based) and moving obstacles (e.g., spiders) interact with the player.
    - Trigger “dying” animations and play corresponding sound effects upon collision.
  - **Power-Ups:**
    - **Mushrooms 🍄:** Grant temporary invincibility.
    - **Guns 🔫:** Enable bullet firing capabilities.
  - **Coins & Scoring 💰:**
    - Coins are dynamically placed in safe areas (via collision checks) and boost the player’s score upon collection.

#### 4. Audio & Visual Effects 🎵🖼️
- **Audio Management:**
  - Uses Pygame’s mixer to handle multiple channels for background music and sound effects (jumping, coin collection, power-ups, etc.).
  - Implements smooth transitions (fade in/out) between audio tracks.
- **Graphics Rendering & UI:**
  - Dynamic rendering of game elements (terrain, obstacles, player, coins) each frame.
  - Uses a camera offset mechanism to keep the player in the center of the action.
  - Displays HUD elements like score and remaining lives.

#### 5. Modular Structure & Asset Management 📂
- **Modularity:**
  - Each component (splash screen, game loop, physics, asset loading) is encapsulated in its own block or class for easier maintenance and potential expansion.
- **Asset Management:**
  - All visual and audio assets are loaded from dedicated folders, scaled appropriately, and used across different game components.
  - Clear segregation of assets ensures that the game remains easily modifiable and adaptable.

### Visual Representation 🗺️

To complement the textual explanation, a professionally designed diagram named **Game Structure.png** is provided. This diagram visually maps out:

- The flow from initialization (splash screen) to the main game loop.
- Interactions between major subsystems (input handling, physics, rendering, audio, and state management).
- The relationship between game entities such as the player, obstacles, coins, power-ups, and dynamic terrain.

The diagram serves as a quick reference for understanding how each part of Bounceario contributes to the overall gameplay experience.

[![Game Structure](https://img.shields.io/badge/View-Game%20Structure-gold?style=for-the-badge&logo=Canva)](https://github.com/StudiYash/RetroFusion/blob/main/Project%20Games/Sub-Project%2001%20-%20Bounceario/Support%20Files/Game%20Structure.png)

---

## Backend Preparation 🔧

### Mark Models Index

The backend development of **Bounceario** was an intricate journey, involving rigorous iterative coding and step-by-step feature integration. Over the course of development, **23 Mark Files** were created each capturing the evolution of the game as new features and improvements were introduced. The 23rd Mark File represents the final, integrated version of the game, consolidating every enhancement and refinement made during this creative process.

---

## Project Backend 🖥️

The backend architecture of **Bounceario** is designed to deliver a dynamic and engaging gameplay experience by integrating various essential components into a unified system. Leveraging **Pygame** for the core game loop and physics, with **Tkinter** for the splash screen, the system handles real-time input processing, realistic physics simulation, dynamic level generation, collision detection, and audio management. Here are the main scenarios managed by the game backend:

1. **Game Loop & Input Handling**:  
   Continuously processes `real-time user inputs` (such as movement, jumping, shooting, and pausing) and updates the game state. The game uses a state machine approach to transition between different states like **Start**, **Playing**, **Paused**, **Respawn/Dying**, and **Game Over**.
2. **Physics & Collision Detection**:  
   Implements realistic physics using gravity and `customizable jump dynamics` (variable jump height via a bounce multiplier) for the player's ball. It also features `pixel-perfect collision detection` using Pygame masks to manage interactions between the ball, obstacles, coins, and power-ups.
3. **Dynamic Terrain & Level Generation**:  
   Uses a `Ground Manager` to generate a dynamic terrain with smooth, random curves, and creates floating platforms that provide both challenges and opportunities for bonus pickups. This dynamic level design keeps the gameplay varied and engaging.
4. **Obstacle & Power-Up Management**:  
   Dynamically spawns `obstacles` (both static and moving spiders) and `power-ups` (such as mushrooms for invincibility and guns for shooting) based on the player's progress and distance thresholds. This ensures that the game remains challenging while rewarding quick reflexes and strategic movements.
5. **Coin Spawning & Scoring System**:  
   Coins are strategically placed both on the ground and on platforms using `collision-safe mechanisms` to avoid interference with obstacles. When collected, coins boost the player's score, thereby enhancing the overall reward system of the game.
6. **Audio Management & Visual Rendering**:  
   Leverages `Pygame's mixer` to manage multiple audio channels for background music and sound effects (e.g., jumping, coin collection, collisions, and power-ups) with smooth fade transitions. Additionally, the backend handles the `real-time rendering` of the dynamic landscape, obstacles, game characters, and HUD elements like score and lives.

The integrated code combines all of these components into a cohesive, responsive backend that forms the core of Bounceario's immersive retro gaming experience.

For detailed information, visit the

[![Explore Project Backend](https://img.shields.io/badge/View-Project%20Backend-white?style=for-the-badge&logo=github)](https://github.com/StudiYash/RetroFusion/tree/main/Project%20Games/Sub-Project%2001%20-%20Bounceario/Project%20Backend)

---

## Project Frontend 🎨

The **Project Frontend** focuses on delivering a user-friendly and aesthetically pleasing interface for Bounceario.  

### Main Page Features:
- 🌟 Maximized window view.
- 🎨 Dark-themed interface with dynamic logo resizing.
- ✨ Hover-responsive buttons.

For detailed instructions, visit the 

[![Explore Project Frontend](https://img.shields.io/badge/View-Project%20Frontend-pink?style=for-the-badge&logo=github)](https://github.com/StudiYash/RetroFusion/tree/main/Project%20Games/Sub-Project%2001%20-%20Bounceario/Project%20Frontend)

---

## Project Windows Application ✨

### Installer Steps:
1. **Language Selection**: Choose preferred language.
2. **License Agreement**: Accept terms.
3. **Installation Progress**: Relax while the app installs.

**📥 Download Bounceario**
> Click the button below to download the latest version of Bounceario.

[![Bounceario Windows Application](https://img.shields.io/badge/View-Download%20Bounceario%20Windows%20Application-gold?style=for-the-badge&logo=GitHub)](https://github.com/StudiYash/RetroFusion/blob/main/Project%20Games/Sub-Project%2001%20-%20Bounceario/Project%20Windows%20Application/Bounceario.exe)

For more information about Project Windows Application, visit the 

[![Project Windows Application](https://img.shields.io/badge/View-Project%20Windows%20Application-indigo?style=for-the-badge&logo=github)](https://github.com/StudiYash/RetroFusion/tree/main/Project%20Games/Sub-Project%2001%20-%20Bounceario/Project%20Windows%20Application)

---

## License 📄

This game is a subproject of the **RetroFusion** open-source umbrella project and is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/).

By using, modifying, or sharing this game, you agree to the following conditions:
- **Attribution:** You must provide appropriate credit to both the RetroFusion project and the original contributor(s) of this game.
- **Non-Commercial Use:** The game and its contents may not be used for commercial purposes without explicit permission.
- **ShareAlike:** Any adaptations or derivative works must be distributed under the same CC BY-NC-SA 4.0 license.

**Attribution Example:**  
"**Bounceario** – a RetroFusion game by Yash Shukla. See [CONTRIBUTORS.md](https://github.com/StudiYash/RetroFusion/blob/main/CONTRIBUTORS.md) for the complete list of contributors."

For complete license details, please see the [LICENSE](https://github.com/StudiYash/RetroFusion/blob/main/LICENSE) file in the RetroFusion repository.

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

---

## Disclaimer ⚠️

This game is a subproject of the **RetroFusion** open-source umbrella project and is intended solely for non-commercial, educational, and creative purposes. All content—including code, art, sound, and design—is provided "as-is" and is meant to serve as a learning platform and a celebration of retro gaming culture.

Any similarities between elements of this game and copyrighted or trademarked material owned by third parties are purely coincidental or intended as homage. RetroFusion is not affiliated with, endorsed by, or in any way associated with any external companies or organizations.

If you believe that any portion of this game infringes on your intellectual property rights, please contact us immediately at [studiyash@gmail.com](mailto:studiyash@gmail.com). We are committed to reviewing all claims promptly and taking appropriate corrective action.

By using, modifying, or sharing this game, you acknowledge that it is for personal, educational, and non-commercial use only.

---

## Copyright ©️

All original content—including code, art assets, designs, and other creative elements—created for this game is the intellectual property of its respective contributors and forms an integral part of the **RetroFusion** umbrella project. This game is distributed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/), which permits non-commercial use, modification, and sharing, provided that appropriate credit is given and any derivatives are shared under the same terms.

While you are encouraged to explore, learn from, and build upon this work for personal or educational purposes, any commercial use or unauthorized exploitation of this content is strictly prohibited. Unauthorized use, including any attempt to claim ownership or profit from this work without explicit permission, may result in legal action.

By using, modifying, or distributing this game, you acknowledge and agree to these terms.

---

## Trademark Disclaimer 🔮

This game is an independent subproject within the **RetroFusion** umbrella, developed solely for educational and non-commercial purposes. Any trademarks, service marks, logos, or brand names appearing in this project are the property of their respective owners. Their inclusion is intended solely for descriptive purposes and as a homage to the rich legacy of retro gaming.

RetroFusion and its subprojects are not endorsed by, affiliated with, or sponsored by any external organizations or trademark holders. The use of any third-party trademarks does not imply any official connection or endorsement.

