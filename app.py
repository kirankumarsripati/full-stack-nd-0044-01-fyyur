#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
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

# connect to a local postgresql database
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

    # implement any missing fields, as a database migration using Flask-Migrate
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

    # implement any missing fields, as a database migration using Flask-Migrate
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

# Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
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
  # Done: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # get venues order by state
  venues = db.session.query(Venue.id, Venue.name, Venue.city, Venue.state).order_by(Venue.state).all()
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
  # implement search on artists with partial string search. Ensure it is case-insensitive.
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
  # replace with real venue data from the venues table, using venue_id

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

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # replace with real data returned from querying the database
  data = db.session.query(Artist.id, Artist.name).all();

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # implement search on artists with partial string search. Ensure it is case-insensitive.
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
  # replace with real venue data from the venues table, using venue_id

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
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
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
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with r-eal venues data.
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
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
