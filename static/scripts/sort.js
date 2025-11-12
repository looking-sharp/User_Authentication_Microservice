const sortOptionsDiv = document.getElementById("sort-list");
const sortButton = document.getElementById("sortByBtn");
var sortOptions = ["Oldest", "Newest"];
var divShowing = false;

/** This function formatts an isoString to a date string
 * 
 * @param {string} isoString 
 * @returns dateString
 */
function formatISODate(isoString) {
    if (!isoString) return "null"; // handle null values

    const date = new Date(isoString);
    const options = { 
        year: 'numeric', month: 'long', day: 'numeric',
        hour: '2-digit', minute: '2-digit', hour12: true 
    };
    return date.toLocaleString('en-US', options); 
}

/** This function sorts the current list of emails
 *  based on oldest, newest, or email status
 * 
 * @param {string} sortingMethod 
 */
function sortEmailsBy(sortingMethod) {
    const userEntries = Array.from(document.querySelectorAll('.user-entry'));
    if (userEntries.length === 0) return;

    let sorted = [];

    switch (sortingMethod) {
        case "Newest":
            sorted = userEntries.sort((a, b) => {
                const dateA = new Date(a.querySelector('.created_at').textContent.replaceAll('"',''));
                const dateB = new Date(b.querySelector('.created_at').textContent.replaceAll('"',''));
                return dateB - dateA; // newest first
            });
            break;

        case "Oldest":
            sorted = userEntries.sort((a, b) => {
                const dateA = new Date(a.querySelector('.created_at').textContent.replaceAll('"',''));
                const dateB = new Date(b.querySelector('.created_at').textContent.replaceAll('"',''));
                return dateA - dateB; // oldest first
            });
            break;

        default:
            console.warn("Unknown sorting method:", sortingMethod);
            return;
    }

    const parent = userEntries[0].parentElement;
    sorted.forEach(el => parent.appendChild(el));

    toggleDivDisplay();
}

/* Create all the sort options dynamically */
document.addEventListener('DOMContentLoaded', () => {
    sortOptions.forEach(option => {
        const div = document.createElement('div');
        div.textContent = option;

        div.addEventListener('click', () => {
            sortEmailsBy(option);
        });

        sortOptionsDiv.appendChild(div);
    });
});

/* Toggle the sort dropdown display */
function toggleDivDisplay() {
    divShowing = !divShowing;
    sortOptionsDiv.style.display = divShowing ? "block" : "none";
    const sortArrow = document.getElementById("sortArrow");
    if(sortArrow) sortArrow.classList.toggle("open");
}

sortButton.addEventListener('click', () => {
    toggleDivDisplay();
});
