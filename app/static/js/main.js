// Initialisation des comportements dynamiques

document.addEventListener('DOMContentLoaded', () => {
    // 1. Disparition automatique des messages Flash après 4 secondes
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 4000);
    });

    // 2. Recherche en temps réel dans la table des étudiants (Panneau Admin)
    const searchInput = document.getElementById('student-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#student-table-body tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});

// 3. Gestion des Modaux Customisés (Vanilla JS)
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Empêche le scroll en arrière-plan
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// Fermeture du modal en cliquant à l'extérieur du contenu
window.addEventListener('click', (e) => {
    if (e.target.classList.contains('custom-modal-overlay')) {
        e.target.style.display = 'none';
        document.body.style.overflow = '';
    }
});

// 4. Charger et Préremplir le Modal de Modification Étudiant via API
function openEditStudentModal(userId) {
    // Appel AJAX sur l'API sécurisée pour récupérer les données de l'étudiant
    fetch(`/api/student/${userId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Erreur lors de la récupération des données de l'étudiant");
            }
            return response.json();
        })
        .then(data => {
            // Remplir les champs du formulaire
            const form = document.getElementById('edit-student-form');
            if (form) {
                form.action = `/admin/student/edit/${userId}`;

                document.getElementById('edit-email').value = data.email;
                document.getElementById('edit-matricule').value = data.profile.matricule || '';
                document.getElementById('edit-nom').value = data.profile.nom || '';
                document.getElementById('edit-prenom').value = data.profile.prenom || '';
                document.getElementById('edit-filiere').value = data.profile.filiere || '';

                // Gérer les boutons radio de boursier
                const estBoursierVal = data.profile.est_boursier ? '1' : '0';
                const boursierRadios = form.querySelectorAll('input[name="est_boursier"]');
                boursierRadios.forEach(radio => {
                    if (radio.value === estBoursierVal) radio.checked = true;
                });

                // Gérer les boutons radio de statut actif
                const isActiveVal = data.is_active ? '1' : '0';
                const activeRadios = form.querySelectorAll('input[name="is_active"]');
                activeRadios.forEach(radio => {
                    if (radio.value === isActiveVal) radio.checked = true;
                });

                // Ouvrir le modal
                openModal('edit-student-modal');
            }
        })
        .catch(err => {
            console.error(err);
            alert("Impossible de charger les données de l'étudiant. Veuillez réessayer.");
        });
}

// 5. Ouvrir le Modal de Réinitialisation de Mot de Passe
function openResetPwdModal(userId, email) {
    const form = document.getElementById('reset-pwd-form');
    if (form) {
        form.action = `/admin/student/reset-password/${userId}`;
        document.getElementById('reset-student-email').textContent = email;
        openModal('reset-pwd-modal');
    }
}
