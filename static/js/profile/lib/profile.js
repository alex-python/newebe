(function() {
  var ProfileView, User, UserCollection, profileApp;
  var __hasProp = Object.prototype.hasOwnProperty, __extends = function(child, parent) {
    for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; }
    function ctor() { this.constructor = child; }
    ctor.prototype = parent.prototype;
    child.prototype = new ctor;
    child.__super__ = parent.prototype;
    return child;
  };
  User = (function() {
    __extends(User, Backbone.Model);
    User.prototype.url = '/user/';
    function User(user) {
      User.__super__.constructor.apply(this, arguments);
      this.id = "";
      this.set("url", user.url);
      this.set("name", user.name);
      this.set("description", user.description);
    }
    /* Setters / Accessors */
    User.prototype.getName = function() {
      return this.get("name");
    };
    User.prototype.setName = function(name) {
      alert(name);
      this.set("name", name);
      return alert(this.getName());
    };
    User.prototype.getUrl = function() {
      return this.get("userUrl");
    };
    User.prototype.setUrl = function(url) {
      return this.set("url", url);
    };
    User.prototype.getDescription = function() {
      return this.get("description");
    };
    User.prototype.setDescription = function(description) {
      return this.set("description", description);
    };
    User.prototype.isNew = function() {
      return false;
    };
    return User;
  })();
  /* Model for a User collection */
  UserCollection = (function() {
    function UserCollection() {
      UserCollection.__super__.constructor.apply(this, arguments);
    }
    __extends(UserCollection, Backbone.Collection);
    UserCollection.prototype.model = User;
    UserCollection.prototype.url = '/user/';
    UserCollection.prototype.parse = function(response) {
      return response.rows;
    };
    return UserCollection;
  })();
  ProfileView = (function() {
    __extends(ProfileView, Backbone.View);
    ProfileView.prototype.el = $("#profile");
    function ProfileView() {
      ProfileView.__super__.constructor.apply(this, arguments);
    }
    ProfileView.prototype.initialize = function() {
      _.bindAll(this, 'onKeyUp', 'postUserInfo', 'fetch', 'addAll');
      this.users = new UserCollection;
      return this.users.bind('refresh', this.addAll);
    };
    /* Events */
    ProfileView.prototype.onKeyUp = function(event) {
      this.postUserInfo();
      return event;
    };
    /* Functions */
    ProfileView.prototype.addAll = function() {
      this.users;
      this.user = this.users.first();
      $("#platform-profile-name").val(this.user.getName());
      $("#profile-description").val(this.user.getDescription());
      $("#platform-profile-url").val(this.user.get("url"));
      if (!this.user.get("url")) {
        this.tutorialOn = true;
        this.displayTutorial(1);
      }
      return this.users;
    };
    ProfileView.prototype.fetch = function() {
      this.users.fetch();
      return this.users;
    };
    ProfileView.prototype.postUserInfo = function() {
      var tutorialOn;
      $("#profile").addClass("modified");
      tutorialOn = this.tutorialOn;
      return this.user.save({
        name: $("#platform-profile-name").val(),
        url: $("#platform-profile-url").val(),
        description: $("#profile-description").val()
      }, {
        success: function() {
          if (tutorialOn) {
            $.get("/profile/tutorial/2/", function(data) {
              return $("#tutorial-profile").html(data);
            });
          }
          return $("#profile").removeClass("modified");
        }
      });
    };
    ProfileView.prototype.testTutorial = function() {
      if (this.tutorialOn) {
        this.displayTutorial(2);
        this.tutorialOn = false;
      }
      return false;
    };
    ProfileView.prototype.displayTutorial = function(index) {
      return $.get("/profile/tutorial/" + index + "/", function(data) {
        return $("#tutorial-profile").html(data);
      });
    };
    /* UI Builders */
    ProfileView.prototype.setListeners = function() {
      $("#platform-profile-name").keyup(function(event) {
        return profileApp.onKeyUp(event);
      });
      $("#platform-profile-url").keyup(function(event) {
        return profileApp.onKeyUp(event);
      });
      return $("#profile-description").keyup(function(event) {
        return profileApp.onKeyUp(event);
      });
    };
    ProfileView.prototype.setWidgets = function() {
      $("#profile input").val(null);
      return $("#profile-a").addClass("disabled");
    };
    return ProfileView;
  })();
  profileApp = new ProfileView;
  profileApp.setWidgets();
  profileApp.setListeners();
  profileApp.fetch();
}).call(this);
