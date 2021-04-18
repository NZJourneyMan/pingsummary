var app = new Vue({ 
    el: '#app', 
    data() {
        return {
            pickedDate: "",
            imageFile: ""
        };
    },
    methods: {
        submit() {
            if (this.pickedDate) {
                this.imageFile = '/static/images/' + this.pickedDate + ".png?dummy=" + Math.random();
            }
        },
        brokenImage() {
            this.imageFile = "";
        },
    }
})