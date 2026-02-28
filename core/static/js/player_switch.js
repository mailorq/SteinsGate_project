document.addEventListener("DOMContentLoaded", () => {
    const btnMain = document.getElementById("btn-main");
    const btnBackup = document.getElementById("btn-backup");
    const playerMain = document.getElementById("player-main");
    const playerBackup = document.getElementById("player-backup");
    const indicator = document.getElementById("player-indicator");

    btnMain.onclick = () => {
        indicator.style.transform = "translateX(0%)";

        playerMain.classList.add("active");
        playerBackup.classList.remove("active");
    };

    btnBackup.onclick = () => {
        indicator.style.transform = "translateX(100%)";

        playerBackup.classList.add("active");
        playerMain.classList.remove("active");
    };
});
