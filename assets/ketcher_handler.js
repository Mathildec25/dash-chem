/*
This code handles the interaction with the Ketcher chemical editor embedded in a Dash application.
It listens for messages from the Ketcher iframe, retrieves SMILES data, and stores it
*/

window.addEventListener('message', function (event) {
    if (event.data === 'get-smiles') {
        const iframe = document.getElementById('ketcher-frame');
        const ketcher = iframe?.contentWindow?.ketcher;

        if (ketcher) {
            ketcher.getSmiles().then(function (smiles) {
                console.log("SMILES extracted:", smiles);
                localStorage.setItem("ketcher_latest_smiles", smiles);
                // No clear/reset of canvas!
            });
        }
    }
});
