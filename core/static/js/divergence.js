// static/js/divergence.js

class DivergenceMeter {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        this.digits = this.container.querySelectorAll('.nixie-digit');
        this.isAnimating = false;
    }

    setValue(value) {
        const clean = value.replace(/[^0-9]/g, '');
        this.digits.forEach((el, i) => {
            if (clean[i] !== undefined) el.innerText = clean[i];
        });
    }

    animate(targetValue, duration = 800, callback = null) {
        if (this.isAnimating) return;
        this.isAnimating = true;

        const startTime = Date.now();

        const interval = setInterval(() => {
            this.digits.forEach(el => {
                el.innerText = Math.floor(Math.random() * 10);
                el.classList.toggle('flicker', Math.random() > 0.8);
            });

            if (Date.now() - startTime >= duration) {
                clearInterval(interval);
                this.setValue(targetValue);
                this.digits.forEach(el => el.classList.remove('flicker'));
                this.isAnimating = false;
                if (callback) callback();
            }
        }, 40);
    }
}