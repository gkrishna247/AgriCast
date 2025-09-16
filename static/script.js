// static/script.js
document.addEventListener('DOMContentLoaded', function () {
    const cropButtons = document.querySelectorAll('.crop-button');
    const selectAllButton = document.querySelector('.select-all-button');
    const selectedCropsInput = document.getElementById('selected_crops');
    const predictionForm = document.querySelector('form');
    const loader = document.getElementById('loader');
    const predictionResultSection = document.querySelector('.prediction-result');

    function updateSelectedCropsInput() {
        const selectedCrops = Array.from(document.querySelectorAll('.crop-button.selected')).map(button => button.dataset.crop);
        selectedCropsInput.value = JSON.stringify(selectedCrops);
    }

    function updateSelectAllButtonState() {
        const allSelected = Array.from(cropButtons).length > 0 && Array.from(cropButtons).every(button => button.classList.contains('selected'));
        if (selectAllButton) {
            selectAllButton.classList.toggle('selected', allSelected);
            selectAllButton.textContent = allSelected ? 'Deselect All' : 'Select All';
        }
    }

    cropButtons.forEach(button => {
        button.addEventListener('click', function () {
            this.classList.toggle('selected');
            updateSelectAllButtonState();
            updateSelectedCropsInput();
        });
    });

    if (selectAllButton) {
        selectAllButton.addEventListener('click', function () {
            const isSelected = this.classList.contains('selected');
            cropButtons.forEach(button => {
                button.classList.toggle('selected', !isSelected);
            });
            updateSelectAllButtonState();
            updateSelectedCropsInput();
        });
    }

    if (predictionForm) {
        predictionForm.addEventListener('submit', function () {
            if (loader) {
                loader.style.display = 'block';
            }
            if (predictionResultSection) {
                predictionResultSection.style.display = 'none';
            }
        });
    }

    // Initial state setup
    updateSelectedCropsInput();
    updateSelectAllButtonState();

    // Chart.js implementation
    const ctx = document.getElementById('priceChart');
    if (ctx && typeof chartData !== 'undefined' && chartData.labels.length > 0) {
        const datasets = chartData.datasets.map(ds => ({
            label: ds.label,
            data: ds.data,
            borderColor: ds.borderColor,
            backgroundColor: ds.backgroundColor,
            fill: false,
            tension: 0.1
        }));

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Price'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }
});
