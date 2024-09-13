<h2>2D Platformer game coupled with evolutionary algorithm</h2>

<h4>Game overview</h4>
This is a a simple 2D game I created using the pygame library a few years ago in which the player has to navigate around the map dodging lava and moving enemies to reach the exit.
<br>
After learning about AI models in university, I decided to come back to this project and implement an evolutionary algorithm to beat my game.

<li><h4>The Evolutionary algorithm</h4>
<ul>An individual represents a single try at completing the level</ul>
<ul>Genes are represesented as a single moved performed by the model in the game (left, right, jump) </ul>
  <ul>The evolution function is where i've had to do the most experimenting. In the end, I decided a checkpoint reward-penalization based system is the best option for the model</ul>
</li>

Currently, the model I have saved here has not yet been able to complete the level.
<br>
In the future I plan to use NVIDIA CUDA to accelerate the process of learning.
