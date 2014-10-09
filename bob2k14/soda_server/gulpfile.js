var gulp = require('gulp');
var ts = require('gulp-type');
var tsd = require('gulp-tsd');
var sourcemaps = require('gulp-sourcemaps');
var del = require('del');
var transform = require('vinyl-transform');
var browserify = require('browserify');
var uglify = require('gulp-uglify');
var rename = require('gulp-rename');
var sass = require('gulp-ruby-sass');
var autoprefix = require('gulp-autoprefixer');
var notify = require('gulp-notify');
var bower = require('gulp-bower');
var fileinclude = require('gulp-file-include');

var tsProject = ts.createProject({
    declarationFiles: true,
    noExternalResolve: true,
    sortOutput: true,
    module: "commonjs"
});

//uncomment to turn on browserifyshim diags
//process.env.BROWSERIFYSHIM_DIAGNOSTICS=1;

gulp.task('ts-compile', ['ts-typings'], function () {
    var tsResult = gulp.src(['src/*.ts', 'typings/**/*.ts'])
                       .pipe(sourcemaps.init())
                       .pipe(ts(tsProject));
    tsResult.dts.pipe(gulp.dest('build/definitions'));
    return tsResult.js.pipe(sourcemaps.write())
                      .pipe(gulp.dest('build'));
})

gulp.task('ui-ts-compile', ['ts-typings'], function () {
    var browserified = transform(function(filename)
                                 {
                                     return browserify(filename, {debug: true})
                                            .plugin('tsify', { module: 'commonjs', target: 'ES5'})
                                            .bundle()
                                 })

    return gulp.src(['ui_src/client.ts'])
               .pipe(browserified)
//               .pipe(uglify({outSourceMap:true}))
               .pipe(rename({
                   extname: ".js"
               }))
               .pipe(gulp.dest('build/ui/scripts'));
})

gulp.task('ts-typings', function (cb) {
    tsd({
        command: 'reinstall',
        config: './tsd.json'
    },cb);
});

gulp.task('bower', function()
          {
              return bower()
                     .pipe(gulp.dest('./bower_components'));
          }
         );

gulp.task('icons', ['bower'], function()
          {
            return gulp.src('./bower_components/fontawesome/fonts/**.*')
                       .pipe(gulp.dest('./build/ui/fonts'));
          });

gulp.task('images', ['bower'], function()
          {
            return gulp.src('./images/**/*.*')
                       .pipe(gulp.dest('./build/ui/images'));
          });

gulp.task('html', function()
          {
              return gulp.src('./ui_src/*.html')
                         .pipe(fileinclude({
                             prefix: '@@',
                             basepath: './ui_src/htinclude/'
                         }))
                         .pipe(gulp.dest('./build/ui'));
          })
gulp.task('css', ['bower'], function()
          {
              return gulp.src('./ui_src/style.scss')
                         .pipe(sass({
                            style: 'compressed',
                            loadPath: [
                                './ui_src',
                                './bower_components/bootstrap-sass-official/assets/stylesheets/',
                                './bower_components/fontawesome/scss/'
                            ]
                         }))
                         .pipe(autoprefix('last 2 version'))
                         .pipe(gulp.dest('./build/ui/css'))
          })

gulp.task('clean', function(cb) {
    del(['build', 'typings'], cb);
});

gulp.task('default', function() {
    gulp.start('bower', 'html', 'icons', 'css', 'images', 'ui-ts-compile', 'ts-compile', 'ts-typings');
});

gulp.task('watch', ['ts-compile'], function() {
    gulp.watch('src/*.ts', ['ts-compile']);
});
