
let players = [];

function addPlayer (){
    const name = document.getElementById("playerName").value;
    if (name === ''){

    };
    const player = {
        name:name,
        score:0
    };
    players.push(player);
    updatePlayersList();
    document.getElementById('playerName').value='';

};

function updatePlayersList() {
    const playerList = document.getElementById("playersList");
    playerList.innerHTML = '';
    players.forEach((player, index) => {
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
        playersList.appendChild(playerDiv);
    });
};

function changeScore(index, isIncrement) {
    players[index].score += (isIncrement ? 1 : -1);
    document.getElementById(`score-${index}`).innerText = 'Score: ' + players[index].score;
}

function removePlayer(index) {
    players.splice(index, 1);
    updatePlayersList();
}

function orderedSort () {
    players = players.sort((a,b) => b.score - a.score);
    updatePlayersList();
}

document.addEventListener("DOMContentLoaded", () => {

});