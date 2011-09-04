(function(){var a,b,c,d,e=Object.prototype.hasOwnProperty,f=function(a,b){function d(){this.constructor=a}for(var c in b)e.call(b,c)&&(a[c]=b[c]);d.prototype=b.prototype,a.prototype=new d,a.__super__=b.prototype;return a},g=function(a,b){return function(){return a.apply(b,arguments)}};b=function(){function a(b){a.__super__.constructor.apply(this,arguments),this.id="",this.set("url",b.url),this.set("name",b.name),this.set("description",b.description)}f(a,Backbone.Model),a.prototype.url="/user/",a.prototype.getName=function(){return this.get("name")},a.prototype.setName=function(a){alert(a),this.set("name",a);return alert(this.getName())},a.prototype.getUrl=function(){return this.get("userUrl")},a.prototype.setUrl=function(a){return this.set("url",a)},a.prototype.getDescription=function(){return this.get("description")},a.prototype.setDescription=function(a){return this.set("description",a)},a.prototype.isNew=function(){return!1};return a}(),c=function(){function a(){a.__super__.constructor.apply(this,arguments)}f(a,Backbone.Collection),a.prototype.model=b,a.prototype.url="/user/",a.prototype.parse=function(a){return a.rows};return a}(),a=function(){function a(){this.onDescriptionEditClicked=g(this.onDescriptionEditClicked,this),this.onMouseOut=g(this.onMouseOut,this),this.onMouseOver=g(this.onMouseOver,this),a.__super__.constructor.call(this)}f(a,Backbone.View),a.prototype.el=$("#profile"),a.prototype.initialize=function(){_.bindAll(this,"onKeyUp","postUserInfo","fetch","addAll"),this.users=new c,this.isEditing=!1;return this.users.bind("reset",this.addAll)},a.prototype.events={"click #profile-description-edit":"onDescriptionEditClicked","mouseover #profile div.app":"onMouseOver","mouseout #profile div.app":"onMouseOut"},a.prototype.onKeyUp=function(a){this.postUserInfo();return a},a.prototype.onMouseOver=function(a){return $("#profile-description-edit").show()},a.prototype.onMouseOut=function(a){return $("#profile-description-edit").hide()},a.prototype.onDescriptionEditClicked=function(a){this.isEditing?(this.isEditing=!1,$("#profile-preview").fadeOut(function(){return $("#profile-description").slideUp(function(){return $("#profile-description-display").fadeIn()})})):(this.isEditing=!0,$("#profile-description-display").fadeOut(function(){$("#profile-description-display").hide();return $("#profile-description").slideDown(function(){return $("#profile-preview").fadeIn()})}));return!1},a.prototype.addAll=function(){this.users,this.user=this.users.first(),$("#platform-profile-name").val(this.user.getName()),$("#profile-description").val(this.user.getDescription()),$("#platform-profile-url").val(this.user.get("url")),this.renderProfile(),this.user.get("url")||(this.tutorialOn=!0,this.displayTutorial(1));return this.users},a.prototype.fetch=function(){this.users.fetch();return this.users},a.prototype.postUserInfo=function(){var a;$("#profile").addClass("modified"),a=this.tutorialOn,this.user.save({name:$("#platform-profile-name").val(),url:$("#platform-profile-url").val(),description:$("#profile-description").val()},{success:function(){a&&$.get("/profile/tutorial/2/",function(a){return $("#tutorial-profile").html(a)});return $("#profile").removeClass("modified")}});return this.renderProfile()},a.prototype.testTutorial=function(){this.tutorialOn&&(this.displayTutorial(2),this.tutorialOn=!1);return!1},a.prototype.displayTutorial=function(a){return $.get("/profile/tutorial/"+a+"/",function(a){return $("#tutorial-profile").html(a)})},a.prototype.renderProfile=function(){var a,b,c;c=_.template('<h1 class="profile-name"><%= name %></h1>\n<p class="profile-url"><%= url %></p>\n<p class="profile-description"><%= description %></p>'),b=$("#profile-description").val(),a=new Showdown.converter,b=a.makeHtml(b),$("#profile-description-display").html(b),$("#profile-render").html(c({name:$("#platform-profile-name").val(),url:$("#platform-profile-url").val(),description:b}));return this.user},a.prototype.setListeners=function(){$("#platform-profile-name").keyup(function(a){return d.onKeyUp(a)}),$("#platform-profile-url").keyup(function(a){return d.onKeyUp(a)});return $("#profile-description").keyup(function(a){return d.onKeyUp(a)})},a.prototype.setWidgets=function(){$("#profile input").val(null),$("#profile-a").addClass("disabled"),$("#profile-description").hide(),$("#profile-preview").hide(),$("#profile-description-edit").button();return $("#profile-description-edit").hide()};return a}(),d=new a,d.setWidgets(),d.setListeners(),d.fetch()}).call(this)