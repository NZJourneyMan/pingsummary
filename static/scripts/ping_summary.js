var app = new Vue({ 
    el: '#app', 
    data() {
        return {
            pickedDate: "",
            imageFile: "",
            myTimer: null        
        };
    },
    methods: {
        submit() {
            if (this.pickedDate) {
                if (this.myTimer) { 
                    clearInterval(this.myTimer);
                }
                this.myTimer = setTimeout(this.submit, 300000);
                this.imageFile = '/static/images/' + this.pickedDate + ".png?dummy=" + Math.random();
            }
        },
        brokenImage() {
            this.imageFile = "";
            clearInterval(this.myTimer)
            this.myTimer = null;
        },
    }
})