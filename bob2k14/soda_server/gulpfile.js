var gulp = require('gulp');
var ts = require('gulp-type');
var tsd = require('gulp-tsd');
var sourcemaps = require('gulp-sourcemaps');
var del = require('del');
var transform = require('vinyl-transform');
var browserify = require('browserify');
var uglify = require('gulp-uglify');
var rename = require('gulp-rename');

var tsProject = ts.createProject({
    declarationFiles: true,
    noExternalResolve: true,
    sortOutput: true,
    module: "commonjs"
});


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
               .pipe(uglify())
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

gulp.task('clean', function(cb) {
    del(['build', 'typings'], cb);
});

gulp.task('default', function() {
    gulp.start('ui-ts-compile', 'ts-compile', 'ts-typings');
});

gulp.task('watch', ['ts-compile'], function() {
    gulp.watch('src/*.ts', ['ts-compile']);
});
