
let scores = [];

function addScore (){
    const name = document.getElementById("playerName").value;
    if (name === ''){

    };
    const player = {
        name:name,
        score:0
    };
    scores.push(player);
    updatePlayersList();
    document.getElementById('playerName').value='';

};

function updatePlayersList() {
    const playerList = document.getElementById("playersList");
    playerList.innerHTML = '';
    scores.forEach((player, index) => {
        const playerDiv = document.createElement('div');
        playerDiv.innerHTML = `
        <div class="name">
            <a>${player.name}</a>
            <a class="score" id="score-${index}">Score: ${player.score}</a>
        </div>
        <div class="options">
            <button onclick="changeScore(${index}, true)">+</button>
            <button onclick="changeScore(${index}, false)">-</button>
            <button onclick="removePlayer(${index})">del</button>
        </div>
        `;
        playerDiv.setAttribute('class', 'player')
        playerList.appendChild(playerDiv);
    });
};

function changeScore(index, isIncrement) {
    scores[index].score += (isIncrement ? 1 : -1);
    document.getElementById(`score-${index}`).innerText = 'Score: ' + scores[index].score;
}

function removePlayer(index) {
    scores.splice(index, 1);
    updatePlayersList();
}

function orderedSort () {
    scores = scores.sort((a,b) => b.score - a.score);
    updatePlayersList();
}

document.addEventListener("DOMContentLoaded", () => {

});