
const allSideMenu = document.querySelectorAll('#sidebar .side-menu.top li a');

allSideMenu.forEach(item=> {
	const li = item.parentElement;

	item.addEventListener('click', function () {
		allSideMenu.forEach(i=> {
			i.parentElement.classList.remove('active');
		})
		li.classList.add('active');
	})
});




// TOGGLE SIDEBAR
const menuBar = document.querySelector('#content nav .bx.bx-menu');
const sidebar = document.getElementById('sidebar');
let sidebarBtn = document.querySelector(".sidebarBtn");

menuBar.addEventListener('click', function () {
  if(sidebar.classList.toggle('hide'))
{
  sidebarBtn.classList.replace("bx-menu" ,"bx-menu-alt-right");
}else
sidebarBtn.classList.replace("bx-menu-alt-right", "bx-menu");


})







const searchButton = document.querySelector('#content nav form .form-input button');
const searchButtonIcon = document.querySelector('#content nav form .form-input button .bx');
const searchForm = document.querySelector('#content nav form');

searchButton.addEventListener('click', function (e) {
	if(window.innerWidth < 576) {
		e.preventDefault();
		searchForm.classList.toggle('show');
		if(searchForm.classList.contains('show')) {
			searchButtonIcon.classList.replace('bx-search', 'bx-x');
		} else {
			searchButtonIcon.classList.replace('bx-x', 'bx-search');
		}
	}
})







function toggleChevron(element) {
    const chevronIcon = element.querySelector('.chevron-icon');
    chevronIcon.classList.toggle('rotate');
}

$(document).ready(function() {
	// Handle the click on the Products link to toggle the dropdown
	$('#productsLink').on('click', function(e) {
		e.stopPropagation();
		$('#auth').collapse('toggle');
	});
	// Close the dropdown when clicking outside
	$(document).on('click', function(e) {
		if (!$(e.target).closest('#productsLink, #auth').length) {
			$('#auth').collapse('hide');
		}
	});
});













const ctx = document.getElementById('myChart');
	  
new Chart(ctx, {
  type: 'bar',
  data: {
	labels: ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
	datasets: [{
	  label: '# of Votes',
	  data: [12, 19, 3, 5, 2, 3],
	  borderWidth: 1
	}]
  },
  options: {
	scales: {
	  y: {
		beginAtZero: true
	  }
	}
  }
});