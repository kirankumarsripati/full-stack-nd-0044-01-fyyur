#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import SQLALCHEMY_DATABASE_URI
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# DONE: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

@app.template_filter('datetime_fmt')
def format_datetime(value, format='medium'):
  # Source: http://babel.pocoo.org/en/latest/api/dates.html
  # parse date objects instead of parsing from strings
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(value, format)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # DONE: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(db.ARRAY(db.String()))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500), default='')
    shows = db.relationship('Show', backref='Venue', lazy='dynamic')

    def __repr__(self):
      return str({
        'id': self.id,
        'name': self.name,
        'city': self.city,
        'state': self.state,
        'address': self.address,
        'phone': self.phone,
        'image_link': self.image_link,
        'facebook_link': self.facebook_link,
        'genres': self.genres,
        'website': self.website,
        'seeking_talent': self.seeking_talent,
        'seeking_description': self.seeking_description
      })

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # DONE: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500), default='')
    shows = db.relationship('Show', backref='Artist', lazy=True)

    def __repr__(self):
      return str({
        'id': self.id,
        'name': self.name,
        'city': self.city,
        'state': self.state,
        'phone': self.phone,
        'genres': self.genres,
        'image_link': self.image_link,
        'facebook_link': self.facebook_link,
        'website': self.website,
        'seeking_venue': self.seeking_venue,
        'seeking_description': self.seeking_description
      })

# DONE: Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey(Venue.id), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey(Artist.id), nullable=False)
  start_time = db.Column(db.DateTime(timezone=True))

  def __repr__(self):
    return str({
      'id': self.id,
      'venue_id': self.venue_id,
      'artist_id': self.artist_id,
      'start_time': self.start_time,
    })

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # get venues order by state
  venues = db.session.query(Venue.id, Venue.name, Venue.city, Venue.state).order_by(Venue.city, Venue.state).all()
  # temporary variable to compare and group
  venue_state_and_city = ''
  current_time = datetime.now()
  data = []

  for venue in venues:
    num_upcoming_shows = db.session.query(Show.id).filter(Show.venue_id == venue.id, Show.start_time > current_time).count()
    if venue_state_and_city == venue.city + venue.state:
      data[len(data) - 1]['venues'].append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': num_upcoming_shows
      })
    else:
      venue_state_and_city = venue.city + venue.state
      data.append({
        'city':venue.city,
        'state':venue.state,
        'venues': [{
          'id': venue.id,
          'name':venue.name,
          'num_upcoming_shows': num_upcoming_shows
        }]
      })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term = request.form.get('search_term', '');
  venue_query = db.session.query(Venue.id, Venue.name)\
    .filter(Venue.name.ilike('%' + search_term + '%')).all()

  current_time = datetime.now()
  data = []

  for venue in venue_query:
    venue_obj = venue._asdict()
    num_upcoming_shows = db.session.query(Show.id).filter(Show.venue_id == venue.id, Show.start_time > current_time).count()
    venue_obj['num_upcoming_shows'] = num_upcoming_shows
    data.append(venue_obj)

  response = {
    'count': len(data),
    'data': data,
  }

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # DONE: replace with real venue data from the venues table, using venue_id

  selected_venue = Venue.query.get(venue_id)

  if not selected_venue:
    return render_template('errors/404.html')

  selected_venue.past_shows = db.session.query(
    Artist.id.label('artist_id'),
    Artist.name.label('artist_name'),
    Artist.image_link.label('artist_image_link'),
    Show.start_time)\
    .filter(Show.venue_id == venue_id)\
    .filter(Show.artist_id == Artist.id)\
    .filter(Show.start_time <= datetime.now()).all()

  selected_venue.past_shows_count = len(selected_venue.past_shows)

  selected_venue.upcoming_shows = db.session.query(
    Artist.id.label('artist_id'),
    Artist.name.label('artist_name'),
    Artist.image_link.label('artist_image_link'),
    Show.start_time)\
    .filter(Show.venue_id == venue_id)\
    .filter(Show.artist_id == Artist.id)\
    .filter(Show.start_time > datetime.now()).all()

  selected_venue.upcoming_shows_count = len(selected_venue.upcoming_shows)

  return render_template('pages/show_venue.html', venue=selected_venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion

  form = VenueForm()

  if form.validate():
    try:
      new_venue = Venue(
        name = request.form['name'],
        genres = request.form.getlist('genres'),
        address = request.form['address'],
        city = request.form['city'],
        state = request.form['state'],
        phone = request.form['phone'],
        website = request.form['website'],
        facebook_link = request.form['facebook_link'],
        seeking_talent = bool(request.form['seeking_talent']),
        seeking_description = request.form['seeking_description'],
        image_link = request.form['image_link']
      )

      db.session.add(new_venue)
      db.session.commit()

      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except SQLAlchemyError as e:
      # DONE: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed! Please try again later.')
    finally:
      db.session.close()
  else:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed!')
    flash(form.errors)

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # DONE: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion

  message = {}

  try:
    Venue.query.filter_by(id = venue_id).delete()
    db.session.commit()

    message = jsonify({
      'status': 'success',
      'message': 'Venue deleted successfully!'
    })
  except SQLAlchemyError as e:
    message = jsonify({
      'status': 'error',
      'message': 'An error occurred. Venue could not be delete! Please try again later.'
    })
  finally:
    db.session.close()

  # BONUS CHALLENGE DONE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return message

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # DONE: replace with real data returned from querying the database
  data = db.session.query(Artist.id, Artist.name).all();

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form.get('search_term', '');
  artist_query = db.session.query(Artist.id, Artist.name)\
    .filter(Artist.name.ilike('%' + search_term + '%')).all()

  response = {
    'count': len(artist_query),
    'data': artist_query,
  }

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # DONE: replace with real venue data from the venues table, using venue_id

  selected_artist = Artist.query.get(artist_id)

  if not selected_artist:
    return render_template('errors/404.html')

  selected_artist.past_shows = db.session.query(
    Venue.id.label('venue_id'),
    Venue.name.label('venue_name'),
    Venue.image_link.label('venue_image_link'),
    Show.start_time)\
    .filter(Show.venue_id == Venue.id)\
    .filter(Show.artist_id == artist_id)\
    .filter(Show.start_time <= datetime.now()).all()

  selected_artist.past_shows_count = len(selected_artist.past_shows)

  selected_artist.upcoming_shows = db.session.query(
    Venue.id.label('venue_id'),
    Venue.name.label('venue_name'),
    Venue.image_link.label('venue_image_link'),
    Show.start_time)\
    .filter(Show.venue_id == Venue.id)\
    .filter(Show.artist_id == artist_id)\
    .filter(Show.start_time > datetime.now()).all()

  selected_artist.upcoming_shows_count = len(selected_artist.upcoming_shows)

  return render_template('pages/show_artist.html', artist=selected_artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  selected_artist = Artist.query.get(artist_id)
  if not selected_artist:
    return render_template('errors/404.html')

  form.name.data = selected_artist.name
  form.genres.data = selected_artist.genres
  form.city.data = selected_artist.city
  form.state.data = selected_artist.state
  form.phone.data = selected_artist.phone
  form.website.data = selected_artist.website
  form.facebook_link.data = selected_artist.facebook_link
  form.seeking_venue.data = selected_artist.seeking_venue
  form.seeking_description.data = selected_artist.seeking_description
  form.image_link.data = selected_artist.image_link

  # DONE: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=selected_artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # DONE: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  form = ArtistForm()

  if form.validate():
    try:
      artist = Artist.query.get(artist_id)
      artist.name = request.form['name']
      artist.genres = request.form.getlist('genres')
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.website = request.form['website']
      artist.facebook_link = request.form['facebook_link']
      artist.seeking_venue = bool(request.form['seeking_venue'])
      artist.seeking_description = request.form['seeking_description']
      artist.image_link = request.form['image_link']

      db.session.commit()

      # on successful db update, flash success
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except SQLAlchemyError as e:
      # on unsuccessful db update, flash an error instead.
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated! Please try again later.')
    finally:
      db.session.close()
  else:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated!')
    flash(form.errors)

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  selected_venue = Venue.query.get(venue_id)
  if not selected_venue:
    return render_template('errors/404.html')

  form.name.data = selected_venue.name
  form.genres.data = selected_venue.genres
  form.address.data = selected_venue.address
  form.city.data = selected_venue.city
  form.state.data = selected_venue.state
  form.phone.data = selected_venue.phone
  form.website.data = selected_venue.website
  form.facebook_link.data = selected_venue.facebook_link
  form.seeking_talent.data = selected_venue.seeking_talent
  form.seeking_description.data = selected_venue.seeking_description
  form.image_link.data = selected_venue.image_link

  # DONE: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=selected_venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # DONE: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

  form = VenueForm()

  if form.validate():
    try:
      venue = Venue.query.get(venue_id)
      venue.name = request.form['name']
      venue.genres = request.form.getlist('genres')
      venue.address = request.form['address']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.phone = request.form['phone']
      venue.website = request.form['website']
      venue.facebook_link = request.form['facebook_link']
      venue.seeking_talent = bool(request.form['seeking_talent'])
      venue.seeking_description = request.form['seeking_description']
      venue.image_link = request.form['image_link']

      db.session.commit()

      # on successful db update, flash success
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except SQLAlchemyError as e:
      # on unsuccessful db update, flash an error instead.
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated! Please try again later.')
    finally:
      db.session.close()
  else:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated!')
    flash(form.errors)

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion

  form = ArtistForm()

  if form.validate():
    try:
      new_artist = Artist(
        name = request.form['name'],
        genres = request.form.getlist('genres'),
        city = request.form['city'],
        state = request.form['state'],
        phone = request.form['phone'],
        website = request.form['website'],
        facebook_link = request.form['facebook_link'],
        seeking_venue = bool(request.form['seeking_venue']),
        seeking_description = request.form['seeking_description'],
        image_link = request.form['image_link']
      )

      db.session.add(new_artist)
      db.session.commit()

      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except SQLAlchemyError as e:
      # DONE: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed! Please try again later.')
    finally:
      db.session.close()
  else:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed!')
    flash(form.errors)

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  data = db.session.query(
    Venue.id.label('venue_id'),
    Venue.name.label('venue_name'),
    Artist.id.label('artist_id'),
    Artist.name.label('artist_name'),
    Artist.image_link.label('artist_image_link'),
    Show.start_time
  ).filter(Show.venue_id == Venue.id)\
    .filter(Show.artist_id == Artist.id).all()

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # DONE: insert form data as a new Show record in the db, instead
  form = ShowForm()

  if form.validate():
    try:
      show = Show(
        venue_id = request.form['venue_id'],
        artist_id = request.form['artist_id'],
        start_time = request.form['start_time']
      )

      db.session.add(show)
      db.session.commit()

      # on successful db insert, flash success
      flash('Show was successfully listed!')
    except SQLAlchemyError as e:
      flash('An error occurred. Show could not be listed! Please try again later.')
    finally:
      db.session.close()
  else:
    # DONE: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Show could not be listed!')
    flash(form.errors)

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
