const userEntries = document.querySelectorAll(".user-entry");

/** This function toggles the details display from none to
 *  block based on a given user id
 *
 * @param {*} id 
 */
function toggleDetails(id) {
    const details = document.getElementById(`details-${id}`);
    const arrow = document.getElementById(`arrow-${id}`);
    if (details.style.display === "block") {
        details.style.display = "none";
        arrow.classList.remove("open");
    } else {
        details.style.display = "block";
        arrow.classList.add("open");
    }
}

const colapseButton = document.getElementById("colapseBtn");
const expandButton = document.getElementById("expandBtn");

/** This function toggles all details to be none
 *  if they are open when the colapse all button
 *  is pressed
 */
colapseButton.addEventListener('click', () => {
    userEntries.forEach(entry => {
        const details = entry.querySelector(".details");
        if(details.style.display === "block") {
            toggleDetails(details.id.replace("details-", ""))
        }
    });
});

/** This function toggles all details to be block
 *  if they are closed when the expand all button
 *  is pressed
 */
expandButton.addEventListener('click', () => {
    userEntries.forEach(entry => {
        const details = entry.querySelector(".details");
        if(details.style.display === "none") {
            toggleDetails(details.id.replace("details-", ""))
        }
    });
});

const searchButton = document.getElementById("searchBtn");
const filterText = document.getElementById("filter-text");

/** This function filters all of the users
 *  based on a list of commands in /static/autocomplete.js
 *  It looks for 1-1 matches or general matches if the keyword
 *  "INCLUDES" is in the command
 */
function filter() {
    const query = filterText.value.trim();
    if (!query) {
        userEntries.forEach(e => e.style.display = "block");
        return;
    }

    // Split by ":" and remove quotes / "INCLUDES"
    const queryFormatted = query.split(/:(.+)/).map(substr => substr.replace(/"/g, "").replace("INCLUDES", "").trim());
    var key = queryFormatted[0]; // e.g. status_code
    if (key == "created_at") {
        key = "created_at_formatted";
    }
    else if(key == "expires_at") {
        key = "expires_at_formatted";
    }
    const value = queryFormatted[1] ? queryFormatted[1].toLowerCase() : ""; // e.g. 200
    const partial = query.toUpperCase().includes("INCLUDES");
    console.log(`Looking for ${partial ? "partial" : "exact"} match for ${key} with value ${value}`)

    userEntries.forEach(entry => {
        const element = entry.querySelector(`.${key}`);
        let text = element ? element.textContent.replace(/"/g, "").trim() : "";
        console.log(text);

        // Handle null values
        if (text.toLowerCase() === "null") text = "";

        if (partial) {
            // Partial, case-insensitive match
            if (text.toLowerCase().includes(value)) {
                entry.style.display = "block";
            } else {
                entry.style.display = "none";
            }
        } else {
            // Exact match, case-insensitive
            if (text.toLowerCase() === value) {
                entry.style.display = "block";
            } else {
                entry.style.display = "none";
            }
        }
    });
}

/* Allow for user to type enter in place of clucking search button */
filterText.addEventListener('keydown', function(event) {
    if(event.key === "Enter") {
        filter();
    }
});

/* Filter responses when search button is pressed */
searchButton.addEventListener('click', () => {
    filter();
})