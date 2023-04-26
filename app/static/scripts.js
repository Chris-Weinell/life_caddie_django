function turnGreen(target) {
    target.classList.add('green');
}

function turnRed(target) {
    target.classList.add('red');
}

// Controls color of banner display showing the total amount over
// or under budget
overUnder = document.querySelectorAll('.over-under');

for (let element of overUnder) {
    if (element.innerText.includes('Under')) {
        turnGreen(element);
    }
    if (element.innerText.includes('Over')) {
        turnRed(element);
    }
}

// Controls color of Remaining value for the Expense Total on
// the Budget Table.  Turns Red if it is negative.
expenseRemaining = document.querySelectorAll('.expense-remaining');

for (let element of expenseRemaining) {
    if (Number(element.innerText) < 0) {
        turnRed(element);
    }
}


// Scrolls the month-select on the Budget Dashboard to the correct
// month on page load.
window.addEventListener('DOMContentLoaded', (event) => {
    const scrollable = document.querySelector('#month_year_div');
    const scrollItem = document.querySelector(
        '#id_month_year div:has(label input[type="radio"]:checked)'
    )
    const scrollItemParent = scrollItem.parentElement;
    const children = scrollItemParent.children;
    const scrollItemindex = Array.prototype.indexOf.call(children, scrollItem)

    // sets the default scroll to 2 months prior to the 
    // current month as leftmost month in the select.
    scrollable.scrollLeft = (100 * scrollItemindex) - 200;
})