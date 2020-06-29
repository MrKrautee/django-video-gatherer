var VideoPage = function (){

    var state = {
        pagination: {
            previous: null,
            next: null,
            current: window.location.toString(),
        },
        params: {
            order_by: order_by,
            video_lang: video_lang,
            page: page_nr,
        },
        baseUrl: location.protocol + '//' + location.host + location.pathname,
        tagId: null,
        pageTitle: page_title,
    };

    this.change = function(new_state){
        state = new_state;

    };
    this.getState = function(){
        return state;
    };
    this.load = function(){
        return this.loadVideos(this.fullUrl());
    };
    this.fullUrl = function(){
        var url = state.baseUrl + "?" + $.param(state.params);
        return url;
    };
    this.resetPagination = function(){
        state.params.page = 1;
        var pagination = {
            previous : null,
            next: null,
            current: null
        };
        state.pagination = pagination;
    };
    this.toHistory = function(){
        history.pushState(state, state.pageTitle, state.baseUrl);
    };
    this.getVideos = function(url, fnStr){
        return $.get(url, function(data){
            videoHtml = videoTemplate(data);
            $("#content-body")[fnStr](videoHtml);
        }, "json");
    };
    
    //replace content body
    this.loadVideos = function(url){
        var spinner = $("#spinner")
        spinner.show();
        $("#content-body").html("");
        return this.getVideos(url, "html").done(function(data){
            state.pagination.next = data.next;
            state.pagination.previous = data.previous;
            $("#result-count").html(data.count);
            spinner.hide();
        });
    };

    //append content body
    this.loadNextVideos = function(){
        var spinner = $("#spinner")
        spinner.show();
        return this.getVideos(state.pagination.next,
                              "append").done(function(data){
            state.pagination.next = data.next;
            spinner.hide();
        });
    };
    //prepend content body
    this.loadPrevVideos = function(){
        var spinner = $("#spinner-top");
        spinner.show();
        return this.getVideos(state.pagination.previous,
                              "prepend").done(function(data){
            state.pagination.previous = data.previous;
            spinner.hide();
        });
    };
    this.loadByTag = function(tagUrl, tagId){
        this.resetPagination();
        state.baseUrl = tagUrl;
        state.tagId = tagId;
        this.toHistory();
        this.load();
    };
    this.changeOrder = function(orderBy){
        state.params.order_by = orderBy;
        this.resetPagination();
        this.toHistory();
        this.load();
    };
    this.changeLang = function(lang){
        state.params.video_lang = lang;
        this.resetPagination();
        this.toHistory();
        this.load();
    };
}
var page = new VideoPage();

//infinite scroll
var alreadyScrolling = false;
$(window).scroll(function(){
    // get the bottom position
    var bottom_position = $(document).height() - ($(window).scrollTop() + $(window).height());
    // console.log(bottom_position);
    var state = page.getState();
    if(bottom_position<=800 && state.pagination.next !=null &&
       alreadyScrolling == false){
        alreadyScrolling = true;
        page.loadNextVideos().done(function(){
            alreadyScrolling = false;
        });
    }
});
