

document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("collect-smiles-btn");

    if (btn) {
        btn.addEventListener("click", function () {
            console.log("Button clicked — sending get-smiles message to Ketcher");
            window.postMessage("get-smiles", "*");
        });
    }
});