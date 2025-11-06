// Fichier: assets/column_rename.js
// Permet de renommer les colonnes en double-cliquant sur les headers

document.addEventListener('DOMContentLoaded', function() {
    console.log('Column rename script loaded');
    
    // Fonction pour attacher les événements aux headers
    function attachHeaderListeners() {
        // Sélectionner tous les headers de colonnes
        const headers = document.querySelectorAll('.dash-header');
        
        headers.forEach((header, index) => {
            // Éviter les doublons d'événements
            if (header.hasAttribute('data-rename-listener')) {
                return;
            }
            header.setAttribute('data-rename-listener', 'true');
            
            // Double-clic pour renommer
            header.addEventListener('dblclick', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const currentName = this.textContent.trim();
                
                // Créer un input temporaire
                const input = document.createElement('input');
                input.type = 'text';
                input.value = currentName;
                input.style.cssText = `
                    width: 100%;
                    padding: 4px;
                    font-size: 13px;
                    border: 2px solid #007bff;
                    border-radius: 3px;
                    background: white;
                    color: black;
                    font-weight: bold;
                    text-align: center;
                `;
                
                // Remplacer le contenu
                const originalContent = this.innerHTML;
                this.innerHTML = '';
                this.appendChild(input);
                input.focus();
                input.select();
                
                // Fonction pour valider le changement
                const validateChange = () => {
                    const newName = input.value.trim();
                    
                    if (newName && newName !== currentName) {
                        // Mettre à jour le header
                        this.textContent = newName;
                        
                        // Déclencher un événement custom pour Dash
                        const event = new CustomEvent('columnRenamed', {
                            detail: {
                                oldName: currentName,
                                newName: newName,
                                columnIndex: index
                            }
                        });
                        document.dispatchEvent(event);
                        
                        // Afficher notification
                        showNotification(`Column renamed: ${currentName} → ${newName}`, 'success');
                    } else {
                        // Restaurer le contenu original
                        this.innerHTML = originalContent;
                    }
                };
                
                // Valider sur Enter
                input.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        validateChange();
                    } else if (e.key === 'Escape') {
                        header.innerHTML = originalContent;
                    }
                });
                
                // Valider sur perte de focus
                input.addEventListener('blur', function() {
                    validateChange();
                });
            });
            
            // Ajouter tooltip
            header.title = 'Double-click to rename';
        });
    }
    
    // Fonction pour afficher des notifications
    function showNotification(message, type = 'info') {
        // Créer notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            background: ${type === 'success' ? '#28a745' : '#007bff'};
            color: white;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 9999;
            font-size: 14px;
            animation: slideIn 0.3s ease;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Retirer après 3 secondes
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    // Ajouter les animations CSS
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Observer pour réattacher les listeners quand la table se recharge
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                attachHeaderListeners();
            }
        });
    });
    
    // Observer le body pour les changements
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Attacher initialement
    setTimeout(attachHeaderListeners, 500);
    
    // Réattacher périodiquement (au cas où)
    setInterval(attachHeaderListeners, 2000);
});

// Écouter les événements de renommage pour les sauvegarder
document.addEventListener('columnRenamed', function(e) {
    console.log('Column renamed:', e.detail);
    
    // Stocker dans localStorage pour que Dash puisse le récupérer
    const renameData = {
        oldName: e.detail.oldName,
        newName: e.detail.newName,
        timestamp: Date.now()
    };
    
    localStorage.setItem('lastColumnRename', JSON.stringify(renameData));
    
    // Déclencher un événement pour Dash
    window.dispatchEvent(new CustomEvent('dashColumnRenamed'));
});